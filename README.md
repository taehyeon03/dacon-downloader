# Dacon Downloader

Dacon 대회 데이터를 CLI에서 바로 다운로드하는 Python 스크립트입니다.  
Remote 서버나 Colab 등 브라우저 없는 환경에서 유용합니다.

## 설치

```bash
pip install requests
```

## 사용법

```bash
python3 dacon_download.py \
  --email 이메일 \
  --password 비밀번호 \
  --cpt_id 대회ID \
  --output ./data/
```

### 인자 설명

| 인자 | 필수 | 설명 |
|------|------|------|
| `--email` | ✅ | Dacon 로그인 이메일 |
| `--password` | ✅ | Dacon 비밀번호 |
| `--cpt_id` | ✅ | 대회 ID (URL의 숫자 부분) |
| `--output` | ❌ | 저장 디렉토리 (기본값: 현재 폴더) |

### 대회 ID 확인 방법

대회 URL에서 숫자 부분이 `cpt_id`입니다.

```
https://dacon.io/competitions/official/235900/data
                                        ^^^^^^
                                        cpt_id = 235900
```

### 예시

```bash
# 현재 폴더에 다운로드
python3 dacon_download.py --email user@example.com --password mypassword --cpt_id 235900

# 특정 폴더에 다운로드
python3 dacon_download.py --email user@example.com --password mypassword --cpt_id 235900 --output ./dataset/
```

## 주의사항

- **소셜 로그인 전용 계정** (Google/카카오만 사용)은 동작하지 않습니다. Dacon 자체 이메일/비밀번호로 가입한 계정이어야 합니다.
- 대회에 **참가 신청**이 되어 있어야 데이터를 다운로드할 수 있습니다.
- 비밀번호를 커맨드 히스토리에 남기지 않으려면 환경변수를 활용하세요:
  ```bash
  python3 dacon_download.py --email $DACON_EMAIL --password $DACON_PW --cpt_id 235900
  ```

## 동작 원리

Dacon의 내부 REST API(`newapi.dacon.io`)를 역분석하여 구현했습니다.

1. `/login/self_login` — 이메일/비밀번호로 세션 인증
2. `/competition/data?cpt_id=` — 대회 데이터 링크 조회
3. `/competition/download` — 다운로드 로그 기록
4. S3 URL에서 실제 파일 다운로드
