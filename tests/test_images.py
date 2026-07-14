import io
import struct
import zlib
from docx import Document
from core import manuscript_parser, fetcher


def _png(w=3, h=3) -> bytes:
    def chunk(typ, data):
        b = typ + data
        return struct.pack(">I", len(data)) + b + struct.pack(">I", zlib.crc32(b) & 0xffffffff)
    raw = (b"\x00" + b"\x10\x20\x30" * w) * h
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def test_extract_images_from_docx_in_order():
    d = Document()
    d.add_paragraph("첫 문단")
    d.add_picture(io.BytesIO(_png()))
    d.add_paragraph("둘째 문단")
    d.add_picture(io.BytesIO(_png(4, 4)))
    b = io.BytesIO(); d.save(b)
    imgs = manuscript_parser.extract_images(b.getvalue())
    assert len(imgs) == 2
    assert all(isinstance(x, bytes) and x[:8] == b"\x89PNG\r\n\x1a\n" for x in imgs)


def test_extract_images_none():
    d = Document(); d.add_paragraph("이미지 없음")
    b = io.BytesIO(); d.save(b)
    assert manuscript_parser.extract_images(b.getvalue()) == []


def test_extract_image_urls_order_and_lazy():
    html = """
    <div class="se-main-container">
      <img src="https://postfiles.pstatic.net/a.jpg?type=w966">
      <img data-lazy-src="https://postfiles.pstatic.net/b.jpg" src="data:image/gif;base64,zzz">
      <img src="https://ssl.pstatic.net/static/ui-icon.png">
      <img src="https://postfiles.pstatic.net/a.jpg?type=w80">
    </div>"""
    urls = fetcher.extract_image_urls(html)
    assert urls[0].endswith("a.jpg?type=w966")
    assert urls[1] == "https://postfiles.pstatic.net/b.jpg"   # data-lazy-src 우선
    assert not any("ui-icon" in u for u in urls)              # UI 자산 제외
    assert len(urls) == 2                                     # a.jpg 중복 제거
