# Dacon Downloader

Dacon 대회 데이터를 자동으로 다운로드하는 도구입니다.

---

## Remote 서버 사용자 (노트북 → SSH → 서버)

노트북 Chrome의 로그인 쿠키를 자동으로 읽어 원격 서버에서 다운로드합니다.

### 1단계: 노트북에 설치 (처음 한 번만)

노트북 로컬 터미널에서:

```bash
bash <(ssh rtx-5070ti 'cat ~/dacon-downloader/install_notebook.sh')
source ~/.bashrc
```

### 2단계: 다운로드

```bash
dacon 236727
```

끝입니다. Chrome에 dacon.io 로그인이 되어 있으면 자동으로 쿠키를 가져와 서버에서 다운로드합니다.

**옵션:**
```bash
dacon 236727                          # ~/dacon/data 에 저장 (기본)
dacon 236727 --output ~/my/path       # 저장 경로 지정
dacon 236727 --remote other-server    # 다른 SSH 서버 지정
```

> **대회 ID**: URL의 숫자 — `dacon.io/competitions/official/`**`236727`**`/`

---

## 로컬 사용자 (서버에서 직접 실행)

### 설치

```bash
pip install requests
```

### 이메일/비밀번호 (자체 가입 계정)

```bash
python3 dacon_download.py \
  --email 이메일 --password 비밀번호 \
  --cpt_id 236727 --output ./data/
```

### 쿠키 직접 입력 (소셜 로그인 계정)

1. 브라우저 `F12` → Application → Cookies → `dacon.io`
2. 모든 쿠키 값 복사

```bash
python3 dacon_download.py \
  --cookie "connect.sid=값; 다른쿠키=값" \
  --cpt_id 236727 --output ./data/
```

---

## GUI (로컬 데스크탑 환경)

```bash
pip install requests playwright
python3 -m playwright install chromium --with-deps
python3 dacon_gui.py
```

브라우저 창에서 Google/카카오 로그인 후 자동 다운로드.

---

## 주의사항

- 대회에 **참가 신청**이 되어 있어야 다운로드 가능합니다.
- Chrome이 열려 있으면 쿠키 DB가 잠길 수 있습니다. 문제 시 Chrome을 완전히 종료 후 재시도하세요.
