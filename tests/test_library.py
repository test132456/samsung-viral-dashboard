from core import library


def test_library_meta_shape():
    # reference/ 가 비어있으면 None, 파일 있으면 dict(name·updated)
    for meta in (library.terms_meta(), library.guide_meta()):
        assert meta is None or ({"path", "name", "updated"} <= set(meta))


def test_library_bytes_consistent_with_meta():
    assert (library.terms_bytes() is None) == (library.terms_meta() is None)
    assert (library.guide_bytes() is None) == (library.guide_meta() is None)
