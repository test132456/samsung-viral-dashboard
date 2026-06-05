"""네이버 블로그 발행본 수집. extract_text는 순수(테스트 가능), fetch_naver_text는 네트워크."""
from __future__ import annotations
import re
import requests
from bs4 import BeautifulSoup


class FetchError(Exception):
    pass


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


def fetch_naver_text(url: str, timeout: int = 10) -> str:
    """URL → 본문. 네이버는 iframe 구조라 mobile(m.blog) URL로 정규화 후 시도."""
    m = re.search(r"blog\.naver\.com/([^/?]+)/(\d+)", url)
    if m:
        url = f"https://m.blog.naver.com/{m.group(1)}/{m.group(2)}"
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise FetchError(f"수집 실패: {e}") from e
    text = extract_text(resp.text)
    if not text:
        raise FetchError("본문을 찾지 못했습니다. 발행본을 직접 붙여넣어 주세요.")
    return text
