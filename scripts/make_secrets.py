"""서비스계정 JSON → .streamlit/secrets.toml 자동 생성.

사용법:
  python scripts/make_secrets.py "<서비스계정.json 경로>" "<구글시트 URL 또는 ID>" ["<Claude 키(선택)>"]

- private_key 의 줄바꿈 등 까다로운 부분을 알아서 TOML 형식으로 변환합니다.
- 비밀값(private_key 등)은 화면에 출력하지 않고 파일에만 씁니다.
- 결과 파일 .streamlit/secrets.toml 은 .gitignore 되어 저장소에 올라가지 않습니다.
"""
import json
import os
import re
import sys

_FIELDS = ["type", "project_id", "private_key_id", "private_key", "client_email",
           "client_id", "auth_uri", "token_uri", "auth_provider_x509_cert_url",
           "client_x509_cert_url", "universe_domain"]


def _sheet_id(s: str) -> str:
    m = re.search(r"/d/([a-zA-Z0-9\-_]+)", s)
    return m.group(1) if m else s.strip()


def main() -> int:
    if len(sys.argv) < 3:
        print("사용법: python scripts/make_secrets.py \"<서비스계정.json 경로>\" \"<구글시트 URL 또는 ID>\" [Claude키]")
        return 1
    json_path, sheet = sys.argv[1], sys.argv[2]
    claude = sys.argv[3] if len(sys.argv) > 3 else ""
    if not os.path.exists(json_path):
        print(f"❌ JSON 파일을 찾을 수 없어요: {json_path}")
        return 1
    with open(json_path, encoding="utf-8") as f:
        sa = json.load(f)

    lines = [f"SPREADSHEET_ID = {json.dumps(_sheet_id(sheet))}"]
    if claude:
        lines.append(f"ANTHROPIC_API_KEY = {json.dumps(claude)}")
    lines += ["", "[gcp_service_account]"]
    for k in _FIELDS:
        if k in sa:
            lines.append(f"{k} = {json.dumps(sa[k])}")  # json.dumps → 올바른 TOML 문자열(줄바꿈 \n 처리)

    os.makedirs(".streamlit", exist_ok=True)
    out = os.path.join(".streamlit", "secrets.toml")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    email = sa.get("client_email", "(JSON에 client_email 없음)")
    print("✅ 생성 완료 →", out)
    print("📧 서비스계정 이메일:", email)
    print("👉 이 이메일을 대상 구글시트에 '편집자'로 공유했는지 꼭 확인하세요 (안 하면 연결 실패).")
    print("   시트 우측 상단 [공유] → 위 이메일 붙여넣기 → 편집자 → 완료")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
