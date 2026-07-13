# 삼성화재 바이럴 운영 대시보드

삼성화재 다이렉트 바이럴 콘텐츠의 일정 관리, QA 검수, 비교 분석, AI 브리핑을 통합한 Streamlit 대시보드입니다.

---

## 로컬 실행 방법

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 시크릿 파일 생성 (아래 형식 참고)
# .streamlit/secrets.toml 을 직접 작성

# 3. 앱 실행
streamlit run app.py
```

---

## secrets.toml 형식

`.streamlit/secrets.toml` 파일을 아래 형식으로 작성하세요 (git에 커밋하지 않도록 주의):

```toml
SPREADSHEET_ID = "구글시트_ID_여기에_입력"
ANTHROPIC_API_KEY = "sk-ant-..."

[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "key-id"
private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email = "your-sa@your-project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-sa%40your-project.iam.gserviceaccount.com"
```

> 서비스 계정 JSON 파일을 GCP Console → IAM → 서비스 계정에서 발급받은 뒤, 각 필드를 위 형식에 맞게 붙여넣으세요.

---

## 배포 (Streamlit Community Cloud · 무료)

`app.py`는 **시크릿이 없으면 내장 기준데이터로 단독 동작**한다(업로드 기반 검수·비교). 즉 구글 설정 없이 바로 배포된다.

**기본 배포 (시트 없이 · 시크릿 불필요)**
1. [share.streamlit.io](https://share.streamlit.io) → **Continue with GitHub** 로그인.
2. **Create app → Deploy a public app from GitHub**.
3. 값 입력:
   - Repository: `test132456/samsung-viral-dashboard`
   - Branch: `master`
   - **Main file path: `app.py`**
4. (Advanced settings) **Python version: 3.12** 권장.
5. **Deploy** → 1~2분 후 `https://<앱이름>.streamlit.app` 발급. 이후 `master` push 시 자동 재배포.

> 이 상태에서 심의전 원고 검수·원고↔발행물 비교는 완전히 동작한다. AI 노출현황 탭은 샘플로 표시된다.

**(선택) 나중에 구글시트로 기준·AI노출 기록 관리**
- `scripts/make_secrets.py` 로 서비스계정 JSON → `secrets.toml` 생성 후, Advanced settings → **Secrets** 에 그 내용을 붙여넣는다.
- 서비스계정 이메일(`...@....iam.gserviceaccount.com`)을 대상 구글시트에 **편집자로 공유**한다.
- 시크릿이 감지되면 자동으로 시트 연결 모드로 전환된다. (Claude 키 `ANTHROPIC_API_KEY` 를 넣으면 AI 2차검수 활성)

```toml
SPREADSHEET_ID = "..."
ANTHROPIC_API_KEY = "sk-ant-..."   # 없으면 생략

[gcp_service_account]
type = "service_account"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@....iam.gserviceaccount.com"
# (나머지 JSON 필드 그대로)
```

> ⚠️ Secrets는 레포에 커밋하지 말 것(`.streamlit/secrets.toml` 은 `.gitignore` 처리됨). Cloud Secrets 입력창에만 넣는다.

---

## 폴더 구조

```
samsung-viral-dashboard/
├── app.py                  # 앱 진입점
├── requirements.txt
├── .streamlit/
│   └── config.toml         # 테마·서버 설정 (secrets.toml은 git 제외)
├── core/
│   ├── schema.py           # 시트명·컬럼명·상태값 상수
│   └── sheets.py           # Google Sheets 데이터 계층
├── views/                  # 탭별 UI 모듈
├── tests/                  # pytest 테스트
└── scripts/                # 시드·유틸 스크립트
```
