#!/usr/bin/env python3
"""
Dacon 대회 데이터 다운로드 스크립트

[방법 1] 이메일/비밀번호 (Dacon 자체 가입 계정만 가능)
  python3 dacon_download.py --email EMAIL --password PW --cpt_id 대회ID

[방법 2] 쿠키 (Google/카카오 소셜 로그인 계정)
  python3 dacon_download.py --cookie "SESSION=..." --cpt_id 대회ID

cpt_id: 대회 URL의 숫자 (https://dacon.io/competitions/official/235900/ → 235900)
"""

import argparse
import os
import sys
import requests
from pathlib import Path
from urllib.parse import urlparse

API = "https://newapi.dacon.io"

def login_password(session, email, password):
    resp = session.post(f"{API}/login/self_login", json={
        "mail": email,
        "password": password,
        "returnTo": "/",
        "locale": "ko",
    })
    data = resp.json()
    if resp.status_code != 200 or data.get("message") not in ("ok", None):
        print(f"[!] 로그인 실패: {data}")
        print("    Google/카카오 소셜 로그인 계정이라면 --cookie 방식을 사용하세요.")
        sys.exit(1)
    print("[+] 로그인 성공")

def login_cookie(session, cookie_str):
    for item in cookie_str.split(";"):
        item = item.strip()
        if "=" in item:
            k, v = item.split("=", 1)
            session.cookies.set(k.strip(), v.strip(), domain="newapi.dacon.io")
            session.cookies.set(k.strip(), v.strip(), domain="dacon.io")
    # 로그인 확인
    resp = session.get(f"{API}/myinfo/profile")
    if resp.status_code != 200 or resp.json().get("message") == "error":
        print(f"[!] 쿠키 인증 실패. 쿠키가 만료되었거나 잘못되었습니다.")
        print(f"    응답: {resp.json()}")
        sys.exit(1)
    name = resp.json().get("data", {}).get("name", "")
    print(f"[+] 쿠키 인증 성공 (계정: {name})")

def get_data_link(session, cpt_id):
    resp = session.get(f"{API}/competition/data?cpt_id={cpt_id}")
    data = resp.json()
    link = None
    # 여러 응답 구조 대응
    if isinstance(data.get("data"), dict):
        link = data["data"].get("data_link")
    if not link:
        link = data.get("data_link")
    if not link:
        for v in data.values():
            if isinstance(v, dict):
                link = v.get("data_link")
                if link:
                    break
    if not link or link == "null":
        print(f"[!] 데이터 링크 없음. 대회 참가 후 시도해주세요.")
        print(f"    API 응답: {data}")
        sys.exit(1)
    return link

def log_download(session, cpt_id):
    session.post(f"{API}/competition/download", json={"cpt_id": cpt_id})

def download_file(session, url, output_dir):
    filename = urlparse(url).path.split("/")[-1]
    dest = Path(output_dir) / filename
    print(f"[+] 다운로드 중: {filename}")
    with session.get(url, stream=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 // total
                    print(f"\r    {pct}% ({downloaded // 1024 // 1024}MB / {total // 1024 // 1024}MB)", end="", flush=True)
    print(f"\n[+] 저장 완료: {dest}")
    return dest

def main():
    parser = argparse.ArgumentParser(description="Dacon 대회 데이터 다운로드")
    parser.add_argument("--email", help="Dacon 이메일 (자체 가입 계정)")
    parser.add_argument("--password", help="Dacon 비밀번호 (자체 가입 계정)")
    parser.add_argument("--cookie", help="브라우저 쿠키 문자열 (소셜 로그인 계정)")
    parser.add_argument("--cpt_id", required=True, help="대회 ID (URL 숫자)")
    parser.add_argument("--output", default=".", help="저장 디렉토리 (기본: 현재 폴더)")
    args = parser.parse_args()

    if not args.cookie and not (args.email and args.password):
        print("[!] --cookie 또는 (--email + --password) 중 하나가 필요합니다.")
        parser.print_help()
        sys.exit(1)

    os.makedirs(args.output, exist_ok=True)
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Referer": "https://dacon.io/",
        "Origin": "https://dacon.io",
    })

    if args.cookie:
        login_cookie(session, args.cookie)
    else:
        login_password(session, args.email, args.password)

    print(f"[+] 대회 데이터 정보 조회 중... (cpt_id={args.cpt_id})")
    link = get_data_link(session, args.cpt_id)
    print(f"[+] 데이터 링크: {link}")
    log_download(session, args.cpt_id)
    download_file(session, link, args.output)

if __name__ == "__main__":
    main()
