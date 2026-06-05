"""ref_* 시트 초기 채움. 사용:
   python scripts/seed_refs.py            # 기본 금지표현/키워드만 시드
   특약명은 약관 파싱이 필요하므로, 약관 텍스트를 --riders-file 로 전달(줄당 '정식명|오기재1,오기재2')."""
import sys, argparse
import streamlit as st           # secrets 재사용
from core.sheets import Sheets
from core import schema

DEFAULT_BANNED = ["무조건", "전부 보장", "훨씬", "걱정 없이", "모두", "빈번하게",
                  "자주", "는 물론", "뿐만 아니라", "100%", "완벽", "최고"]
DEFAULT_REQUIRED = [("유료광고", "유료광고"),
                    ("본 광고는 상품 가입을 권유하는 목적", "고지")]
DEFAULT_KEYWORDS = [("해외여행보험", "키워드"), ("여행자보험", "키워드"),
                    ("해외여행자보험", "키워드"), ("해외여행보험", "해시태그")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--riders-file", help="줄당 '정식특약명|오기재1,오기재2'")
    args = ap.parse_args()

    info = dict(st.secrets["gcp_service_account"])
    sheets = Sheets(info, st.secrets["SPREADSHEET_ID"])
    sheets.ensure_tabs()

    for t in DEFAULT_BANNED:
        sheets.append(schema.SHEET_REF_BANNED, {"term": t, "note": "seed"})
    for p, ty in DEFAULT_REQUIRED:
        sheets.append(schema.SHEET_REF_REQUIRED, {"phrase": p, "type": ty, "note": "seed"})
    for k, ty in DEFAULT_KEYWORDS:
        sheets.append(schema.SHEET_REF_KEYWORDS, {"keyword": k, "type": ty})

    if args.riders_file:
        with open(args.riders_file, encoding="utf-8") as f:
            for line in f:
                if "|" not in line:
                    continue
                official, mistakes = line.strip().split("|", 1)
                sheets.append(schema.SHEET_REF_RIDERS,
                              {"official_name": official, "common_mistakes": mistakes})
    print("seed 완료")


if __name__ == "__main__":
    main()
