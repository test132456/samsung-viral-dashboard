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

## 배포 (Streamlit Community Cloud)

1. 이 레포를 GitHub에 push
2. [share.streamlit.io](https://share.streamlit.io) 에서 레포 연결
3. **Advanced settings → Secrets** 에 위 `secrets.toml` 내용 전체를 붙여넣기
4. Deploy 클릭

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
