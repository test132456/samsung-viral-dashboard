"""네이버 블로그 발행본 수집. extract_text는 순수(테스트 가능), fetch_naver_text는 네트워크."""
from __future__ import annotations
import re
import requests
from urllib.parse import urlparse, parse_qsl
from bs4 import BeautifulSoup

_UA = "Mozilla/5.0"
# 단축/리다이렉트 링크 도메인 (원본 URL 추적 대상)
_SHORTENERS = ("tinyurl.com", "bit.ly", "naver.me", "me2.do", "buly.kr",
               "abr.ge", "vo.la", "han.gl", "url.kr", "zrr.kr")


class FetchError(Exception):
    pass


def is_shortener(url: str) -> bool:
    return any(s in (url or "") for s in _SHORTENERS)


def parse_link_params(url: str) -> dict:
    """URL 쿼리 파라미터 파싱(순수). 반환:
    {params:[(k,v)...], key:마지막(또는 utm_term) 키, term:추적코드 값}.
    utm_term 이 있으면 그 값을, 없으면 맨 끝 파라미터 값을 term 으로 준다."""
    q = parse_qsl(urlparse(url or "").query, keep_blank_values=True)
    d = dict(q)
    if "utm_term" in d and d["utm_term"]:
        key, term = "utm_term", d["utm_term"]
    elif q:
        key, term = q[-1][0], q[-1][1]
    else:
        key, term = None, None
    return {"params": q, "key": key, "term": term}


def resolve_redirects(url: str, timeout: int = 8) -> str:
    """단축/리다이렉트 링크의 최종 URL 반환(네트워크)."""
    try:
        r = requests.head(url, allow_redirects=True, timeout=timeout, headers={"User-Agent": _UA})
        if r.status_code >= 400 or r.url == url:
            r = requests.get(url, allow_redirects=True, timeout=timeout, headers={"User-Agent": _UA})
        return r.url or url
    except requests.RequestException as e:
        raise FetchError(f"링크 확인 실패: {e}") from e


def extract_text(html: str) -> str:
    """네이버 스마트에디터 본문 영역에서 텍스트 추출."""
    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one(".se-main-container") or soup.body
    if container is None:
        return ""
    paras = container.select(".se-text-paragraph") or container.find_all(["p", "div"])
    lines = [p.get_text(" ", strip=True) for p in paras]
    text = "\n".join(l for l in lines if l)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _normalize_naver_url(url: str) -> str:
    """blog.naver.com/<id>/<no> → m.blog.naver.com/<id>/<no>. 그 외는 원본."""
    m = re.search(r"(?:^|//)(?:m\.)?blog\.naver\.com/([^/?]+)/(\d+)", url)
    if m:
        return f"https://m.blog.naver.com/{m.group(1)}/{m.group(2)}"
    return url


def extract_image_urls(html: str) -> list[str]:
    """네이버 본문(.se-main-container)의 콘텐츠 이미지 URL을 등장 순서대로 추출(순수).
    lazy 로딩 대비 data-lazy-src/src 순으로 보고, UI 아이콘/스티커는 최대한 제외."""
    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one(".se-main-container") or soup.body
    if container is None:
        return []
    urls, seen = [], set()
    for img in container.select("img"):
        src = (img.get("data-lazy-src") or img.get("src") or img.get("data-src") or "").strip()
        if not src.startswith("http"):
            continue
        if "pstatic.net/static" in src or "/dthumb" in src:  # UI/에디터 자산 제외
            continue
        base = src.split("?")[0]
        if base in seen:
            continue
        seen.add(base)
        urls.append(src)
    return urls


def extract_links(html: str) -> list[str]:
    """네이버 본문(.se-main-container)의 바깥 링크(<a href>, 링크카드 포함)를 등장 순서대로 추출(순수)."""
    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one(".se-main-container") or soup.body
    if container is None:
        return []
    out, seen = [], set()
    for a in container.select("a[href]"):
        href = (a.get("href") or "").strip()
        if href.startswith("http") and href not in seen:
            seen.add(href)
            out.append(href)
    return out


def tracking_link_candidates(urls: list[str]) -> list[str]:
    """추적 링크 후보 = 삼성화재 링크 또는 단축 링크."""
    return [u for u in urls if "samsungfire.com" in u or is_shortener(u)]


def fetch_naver_links(url: str, timeout: int = 10) -> list[str]:
    """네이버 발행글 → 본문 바깥 링크 URL 리스트(네트워크)."""
    url = _normalize_naver_url(url)
    try:
        resp = requests.get(url, headers={"User-Agent": _UA}, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise FetchError(f"링크 수집 실패: {e}") from e
    return extract_links(resp.text)


def fetch_naver_images(url: str, timeout: int = 10) -> list[str]:
    """네이버 발행글 → 콘텐츠 이미지 URL 리스트(네트워크)."""
    url = _normalize_naver_url(url)
    try:
        resp = requests.get(url, headers={"User-Agent": _UA}, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise FetchError(f"이미지 수집 실패: {e}") from e
    return extract_image_urls(resp.text)


def fetch_image(url: str, timeout: int = 10) -> bytes:
    """이미지 URL → bytes(네트워크). 네이버 CDN 핫링크 방지 대비 Referer 지정."""
    r = requests.get(url, timeout=timeout,
                     headers={"User-Agent": _UA, "Referer": "https://blog.naver.com/"})
    r.raise_for_status()
    return r.content


def fetch_naver_text(url: str, timeout: int = 10) -> str:
    """URL → 본문. 네이버는 iframe 구조라 mobile(m.blog) URL로 정규화 후 시도."""
    url = _normalize_naver_url(url)
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise FetchError(f"수집 실패: {e}") from e
    text = extract_text(resp.text)
    if not text:
        raise FetchError("본문을 찾지 못했습니다. 발행본을 직접 붙여넣어 주세요.")
    return text
