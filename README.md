# Dacon Downloader

Dacon 대회 데이터를 CLI에서 바로 다운로드하는 Python 스크립트입니다.  
Remote 서버나 Colab 등 브라우저 없는 환경에서 유용합니다.

## 설치

```bash
pip install requests
```

## 사용법

### 방법 1 — 이메일/비밀번호 (Dacon 자체 가입 계정)

```bash
python3 dacon_download.py \
  --email 이메일 \
  --password 비밀번호 \
  --cpt_id 대회ID \
  --output ./data/
```

### 방법 2 — 쿠키 (Google / 카카오 소셜 로그인 계정) ← 소셜 로그인이면 이 방법 사용

**1단계: 브라우저에서 쿠키 복사**

1. 브라우저에서 [dacon.io](https://dacon.io) 로그인
2. 개발자 도구 열기 (`F12`)
3. **Application** 탭 → **Cookies** → `https://dacon.io`
4. `connect.sid` 또는 `sessionId` 값 복사

**2단계: 스크립트 실행**

```bash
python3 dacon_download.py \
  --cookie "connect.sid=복사한값" \
  --cpt_id 대회ID \
  --output ./data/
```

---

### 인자 설명

| 인자 | 필수 | 설명 |
|------|------|------|
| `--email` | 방법1 | Dacon 로그인 이메일 |
| `--password` | 방법1 | Dacon 비밀번호 |
| `--cookie` | 방법2 | 브라우저 쿠키 문자열 |
| `--cpt_id` | ✅ | 대회 ID (URL의 숫자 부분) |
| `--output` | ❌ | 저장 디렉토리 (기본값: 현재 폴더) |

### 대회 ID 확인 방법

```
https://dacon.io/competitions/official/235900/data
                                        ^^^^^^
                                        cpt_id = 235900
```

## 주의사항

- 대회에 **참가 신청**이 되어 있어야 데이터를 다운로드할 수 있습니다.
- 쿠키는 **만료 기한**이 있으므로 오래된 쿠키는 재복사가 필요합니다.
- 비밀번호를 커맨드 히스토리에 남기지 않으려면 환경변수를 사용하세요:
  ```bash
  python3 dacon_download.py --email $DACON_EMAIL --password $DACON_PW --cpt_id 235900
  ```

## 동작 원리

Dacon의 내부 REST API(`newapi.dacon.io`)를 역분석하여 구현했습니다.

1. `/login/self_login` — 이메일/비밀번호로 세션 인증 (자체 계정)
2. `/myinfo/profile` — 쿠키 유효성 검증 (소셜 계정)
3. `/competition/data?cpt_id=` — 대회 데이터 링크 조회
4. `/competition/download` — 다운로드 로그 기록
5. S3 URL에서 실제 파일 다운로드
