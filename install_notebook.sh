#!/usr/bin/env bash
# 노트북에서 한 번만 실행하면 설치 완료
# 사용법: bash <(ssh rtx-5070ti 'cat ~/dacon-downloader/install_notebook.sh')

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
RESET='\033[0m'

log()  { echo -e "${GREEN}${BOLD}[+]${RESET} $*"; }
info() { echo -e "${YELLOW}${BOLD}[*]${RESET} $*"; }

echo
echo -e "${BOLD}Dacon 자동 다운로더 설치${RESET}"
echo "─────────────────────────────"
echo

# 1. dacon_auto.py 복사
log "dacon_auto.py 복사 중..."
scp rtx-5070ti:~/dacon-downloader/dacon_auto.py ~/dacon_auto.py
chmod +x ~/dacon_auto.py

# 2. 의존성 설치
log "Python 패키지 설치 중 (browser-cookie3, secretstorage)..."
pip install -q browser-cookie3 secretstorage

# 3. alias 등록
ALIAS_LINE="alias dacon='python3 ~/dacon_auto.py'"
BASHRC="$HOME/.bashrc"

if grep -q "alias dacon=" "$BASHRC" 2>/dev/null; then
    info "alias dacon 이미 등록되어 있음, 건너뜀"
else
    log "~/.bashrc 에 alias 등록..."
    echo "" >> "$BASHRC"
    echo "# Dacon 데이터 다운로더" >> "$BASHRC"
    echo "$ALIAS_LINE" >> "$BASHRC"
fi

echo
echo -e "${GREEN}${BOLD}✓ 설치 완료!${RESET}"
echo
echo "아래 명령어로 alias를 현재 터미널에 적용하세요:"
echo -e "  ${BOLD}source ~/.bashrc${RESET}"
echo
echo "이후 사용법:"
echo -e "  ${BOLD}dacon 236727${RESET}           # 대회 ID로 다운로드"
echo -e "  ${BOLD}dacon 236727 --output ~/data${RESET}  # 저장 경로 지정"
echo
