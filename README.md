# Dacon Downloader

Dacon 대회 데이터를 쉽게 다운로드하는 도구입니다.  
**GUI 버전**: 브라우저 창이 열리고 로그인 후 자동 다운로드 (Google/카카오 소셜 로그인 지원)  
**CLI 버전**: Remote 서버 등 GUI 없는 환경용

---

## GUI 버전 (권장)

### 설치

```bash
pip install requests playwright
python3 -m playwright install chromium --with-deps
```

### 실행

```bash
python3 dacon_gui.py
```

1. 대회 ID 입력 (예: `235900`)
2. 저장 폴더 선택
3. **"브라우저 열고 로그인 & 다운로드"** 버튼 클릭
4. Chromium 브라우저에서 Google / 카카오로 로그인
5. 로그인 완료 시 브라우저가 자동으로 닫히고 다운로드 시작

---

## Remote 서버 자동 다운로드 (노트북에서 실행)

SSH로 원격 서버에 접속해서 작업하는 경우, **로컬 노트북에서** 이 스크립트를 실행하면 Chrome 쿠키를 자동으로 가져와서 원격 서버에서 다운로드합니다.

### 노트북에서 실행

```bash
# rtx-5070ti에서 스크립트 복사
scp rtx-5070ti:~/dacon-downloader/dacon_auto.py ~/

# 실행 (의존성 자동 설치됨)
python3 ~/dacon_auto.py --cpt_id 236727
```

- Chrome에 dacon.io 로그인이 되어 있어야 합니다
- `--remote` 기본값은 `rtx-5070ti`, 다른 서버면 `--remote 호스트명` 추가
- `--output` 기본값은 `~/dacon/data` (원격 서버 경로)

---

## CLI 버전

### 설치

```bash
pip install requests
```

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
