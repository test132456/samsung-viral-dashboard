"""구글시트 데이터 계층 — 유일한 gspread 접근 지점."""
from __future__ import annotations
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from core import schema

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class Sheets:
    def __init__(self, service_account_info: dict, spreadsheet_id: str):
        creds = Credentials.from_service_account_info(service_account_info, scopes=_SCOPES)
        self._gc = gspread.authorize(creds)
        self._sh = self._gc.open_by_key(spreadsheet_id)

    def ensure_tabs(self) -> None:
        """ALL_SHEETS 탭이 없으면 헤더와 함께 생성."""
        existing = {ws.title for ws in self._sh.worksheets()}
        for name in schema.ALL_SHEETS:
            if name not in existing:
                ws = self._sh.add_worksheet(title=name, rows=200, cols=max(10, len(schema.COLS[name])))
                ws.append_row(schema.COLS[name])

    def read(self, tab: str) -> pd.DataFrame:
        """탭 전체를 DataFrame으로. 빈 탭이면 헤더만 가진 빈 DF."""
        ws = self._sh.worksheet(tab)
        values = ws.get_all_records()
        cols = schema.COLS[tab]
        if not values:
            return pd.DataFrame(columns=cols)
        return pd.DataFrame(values).reindex(columns=cols)

    def overwrite(self, tab: str, df: pd.DataFrame) -> None:
        """탭 전체를 df로 교체(헤더 포함). data_editor 저장용."""
        ws = self._sh.worksheet(tab)
        ws.clear()
        cols = schema.COLS[tab]
        df = df.reindex(columns=cols).fillna("")
        ws.update([cols] + df.astype(str).values.tolist())

    def append(self, tab: str, row: dict) -> None:
        """한 행 추가(qa_results/compare_results/ai_briefing append용)."""
        ws = self._sh.worksheet(tab)
        cols = schema.COLS[tab]
        ws.append_row([str(row.get(c, "")) for c in cols])
