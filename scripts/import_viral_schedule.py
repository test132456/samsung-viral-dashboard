"""'바이럴 일정.xlsx' → calendar_events / distribution 시트 적재.

사용:
   python scripts/import_viral_schedule.py "바이럴 일정.xlsx" --dry-run   # 파싱 결과만 출력
   python scripts/import_viral_schedule.py "바이럴 일정.xlsx"             # 구글시트에 적재
"""
import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import viral_parser, schema


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    events, dist = viral_parser.parse(args.xlsx)
    print(f"달력 이벤트 {len(events)}건 / 배포 {len(dist)}건 파싱됨")
    if args.dry_run:
        for e in events:
            print("  [cal]", e["date"], e["track"], e["task"])
        for d in dist:
            print("  [dist]", d["group"], d["blogger"], d["publish_date"], d["approval_no"][:30])
        return

    import streamlit as st
    from core.sheets import Sheets
    info = dict(st.secrets["gcp_service_account"])
    sheets = Sheets(info, st.secrets["SPREADSHEET_ID"])
    sheets.ensure_tabs()
    for e in events:
        sheets.append(schema.SHEET_CALENDAR, e)
    for d in dist:
        sheets.append(schema.SHEET_DISTRIBUTION, d)
    print("적재 완료")


if __name__ == "__main__":
    main()
