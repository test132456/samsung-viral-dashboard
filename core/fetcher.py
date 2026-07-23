"""네이버 블로그 발행본 수집. extract_text는 순수(테스트 가능), fetch_naver_text는 네트워크."""
from __future__ import annotations
import re
import requests
from urllib.parse import urlparse, parse_qsl, urljoin
from bs4 import BeautifulSoup

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
# 네이버 블로그 수집용 브라우저 헤더(단순 UA는 403으로 자주 막힘)
_NAVER_HEADERS = {
    "User-Agent": _UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    "Referer": "https://blog.naver.com/",
}
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


def resolve_redirects(url: str, timeout: int = 8, max_hops: int = 10) -> str:
    """단축/리다이렉트 링크를 한 홉씩 '수동으로' 따라가 최종 URL 반환.
    - 리다이렉트 주소(Location)에 이미 utm_term 이 보이면 즉시 멈춘다
      → 최종 목적지(광고주 서버, 접속이 느리거나 막히는 곳)에는 접속하지 않는다.
    - 실패해도 예외를 던지지 않고 여기까지 따라온 URL을 반환(그 안에 코드가 있을 수 있음)."""
    cur = url or ""
    try:
        for _ in range(max_hops):
            if "utm_term=" in cur:            # 이미 추적코드가 URL에 있음 → 더 볼 필요 없음
                return cur
            r = requests.get(cur, allow_redirects=False, stream=True, timeout=timeout,
                             headers={"User-Agent": _UA})
            loc = r.headers.get("Location")
            r.close()                          # 본문은 받지 않음(헤더만)
            if not loc:
                return cur                     # 더 이상 리다이렉트 없음
            cur = urljoin(cur, loc)            # 상대경로 Location 대응
        return cur
    except requests.RequestException:
        return cur                             # 타임아웃/차단 시 최선의 URL 반환


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


def _naver_candidates(url: str) -> list[str]:
    """네이버 발행글 수집용 URL 후보(순서대로 시도) — 한쪽이 403이면 다른 형태로 재시도.
    PostView(PC) → 모바일(m.blog) → 원본."""
    m = re.search(r"(?:^|//)(?:m\.)?blog\.naver\.com/([^/?]+)/(\d+)", url or "")
    if m:
        bid, no = m.group(1), m.group(2)
        return [f"https://blog.naver.com/PostView.naver?blogId={bid}&logNo={no}",
                f"https://m.blog.naver.com/{bid}/{no}",
                url]
    return [url]


def _fetch_naver_html(url: str, timeout: int = 10) -> str:
    """네이버 발행글 HTML — 여러 URL 형태 + 브라우저 헤더로 재시도해 본문 컨테이너가 있는 HTML 반환.
    모두 막히면(403 등) FetchError(직접 붙여넣기 안내)."""
    sess = requests.Session()
    last_err = None
    for u in _naver_candidates(url):
        try:
            r = sess.get(u, headers=_NAVER_HEADERS, timeout=timeout)
            r.raise_for_status()
        except requests.RequestException as e:
            last_err = e
            continue
        if "se-main-container" in r.text or "se-text-paragraph" in r.text or "postViewArea" in r.text:
            return r.text
    if last_err:
        raise FetchError(f"수집 실패: {last_err} — 발행본 텍스트를 직접 붙여넣어 주세요.") from last_err
    raise FetchError("본문을 찾지 못했습니다. 발행본 텍스트를 직접 붙여넣어 주세요.")


_STICKER_HOSTS = ("storep-phinf.pstatic.net", "ogqstore", "sticker")


def _cls_has_sticker(value) -> bool:
    if not value:
        return False
    parts = value if isinstance(value, list) else [value]
    return any("sticker" in p for p in parts)


def _is_sticker_img(img) -> bool:
    """네이버 스티커/이모티콘 이미지인지 — 사진(콘텐츠)과 구분해 제외하기 위함."""
    if _cls_has_sticker(img.get("class")):
        return True
    if img.find_parent(class_=_cls_has_sticker):   # se-sticker 컴포넌트 안
        return True
    src = (img.get("data-lazy-src") or img.get("src") or "")
    return any(h in src for h in _STICKER_HOSTS)


def extract_image_urls(html: str) -> list[str]:
    """네이버 본문(.se-main-container)의 콘텐츠 사진 URL을 등장 순서대로 추출(순수).
    스티커/이모티콘·UI 아이콘은 제외해, 심의 원고 사진과 순서가 어긋나지 않게 한다."""
    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one(".se-main-container") or soup.body
    if container is None:
        return []
    urls, seen = [], set()
    for img in container.select("img"):
        if _is_sticker_img(img):   # 스티커/이모티콘 제외
            continue
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
    return extract_links(_fetch_naver_html(url, timeout))


def fetch_naver_images(url: str, timeout: int = 10) -> list[str]:
    """네이버 발행글 → 콘텐츠 이미지 URL 리스트(네트워크)."""
    return extract_image_urls(_fetch_naver_html(url, timeout))


def fetch_image(url: str, timeout: int = 10) -> bytes:
    """이미지 URL → bytes(네트워크). 네이버 CDN 핫링크 방지 대비 Referer 지정."""
    r = requests.get(url, timeout=timeout,
                     headers={"User-Agent": _UA, "Referer": "https://blog.naver.com/"})
    r.raise_for_status()
    return r.content


def fetch_naver_text(url: str, timeout: int = 10) -> str:
    """URL → 본문. PostView(PC)/모바일 등 여러 형태를 브라우저 헤더로 재시도(403 대비)."""
    text = extract_text(_fetch_naver_html(url, timeout))
    if not text:
        raise FetchError("본문을 찾지 못했습니다. 발행본 텍스트를 직접 붙여넣어 주세요.")
    return text
