"""데모용 인메모리 시트 — 구글시트 없이 앱을 돌려보기 위한 Sheets 대체.

production `core.sheets.Sheets`와 동일한 인터페이스(read/overwrite/append/ensure_tabs)를
제공하되, 데이터는 메모리에만 보관한다. 데모/미리보기 전용.
"""
from __future__ import annotations
import pandas as pd
from core import schema


class MockSheets:
    def __init__(self, seed: dict | None = None):
        seed = seed or {}
        self._data: dict[str, pd.DataFrame] = {}
        for tab in schema.ALL_SHEETS:
            cols = schema.COLS[tab]
            rows = seed.get(tab, [])
            df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=cols)
            self._data[tab] = df.reindex(columns=cols).fillna("")

    def ensure_tabs(self) -> None:  # 인터페이스 호환용 (데모는 항상 준비됨)
        return

    def read(self, tab: str) -> pd.DataFrame:
        return self._data[tab].copy()

    def overwrite(self, tab: str, df: pd.DataFrame) -> None:
        cols = schema.COLS[tab]
        self._data[tab] = df.reindex(columns=cols).fillna("").astype(str).reset_index(drop=True)

    def append(self, tab: str, row: dict) -> None:
        cols = schema.COLS[tab]
        new = {c: str(row.get(c, "")) for c in cols}
        self._data[tab] = pd.concat([self._data[tab], pd.DataFrame([new])], ignore_index=True)
