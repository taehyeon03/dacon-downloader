#!/usr/bin/env python3
"""
Dacon 대회 데이터 다운로드 스크립트

[방법 1] 이메일/비밀번호 (Dacon 자체 가입 계정)
  python3 dacon_download.py --email EMAIL --password PW --cpt_id 대회ID

[방법 2] 쿠키 문자열 (소셜 로그인 계정)
  python3 dacon_download.py --cookie "SESSION=..." --cpt_id 대회ID

[방법 3] stdin 파이프 (dacon_auto.py에서 자동 호출)
  echo '{"key":"val"}' | python3 dacon_download.py --cookie-stdin --cpt_id 대회ID
"""

import argparse
import json
import os
import sys
import requests
from pathlib import Path
from urllib.parse import urlparse

API = "https://newapi.dacon.io"


def _make_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Referer": "https://dacon.io/",
        "Origin": "https://dacon.io",
    })
    return session


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
        print("    Google/카카오 계정이라면 dacon_auto.py 를 노트북에서 실행하세요.")
        sys.exit(1)
    print("[+] 로그인 성공")


def login_cookie(session, cookie_str):
    """쿠키 문자열 'k=v; k=v' 파싱 후 세션에 적용"""
    cookie_dict = {}
    for item in cookie_str.split(";"):
        item = item.strip()
        if "=" in item:
            k, v = item.split("=", 1)
            cookie_dict[k.strip()] = v.strip()
    login_cookie_dict(session, cookie_dict)


def login_cookie_dict(session, cookie_dict):
    """쿠키 dict를 세션에 적용하고 로그인 확인"""
    for k, v in cookie_dict.items():
        session.cookies.set(k, v, domain="newapi.dacon.io")
        session.cookies.set(k, v, domain="dacon.io")

    resp = session.get(f"{API}/myinfo/profile")
    body = resp.json()
    if resp.status_code != 200 or body.get("message") == "error":
        print("[!] 쿠키 인증 실패. Chrome에서 dacon.io 로그인 상태인지 확인하세요.")
        print(f"    응답: {body}")
        sys.exit(1)
    data = body.get("data")
    name = data.get("name", "") if isinstance(data, dict) else ""
    print(f"[+] 로그인 확인: {name}")


def get_data_link(session, cpt_id):
    resp = session.get(f"{API}/competition/data?cpt_id={cpt_id}")
    data = resp.json()
    link = None
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
        print("[!] 데이터 링크 없음. 대회 참가 후 시도해주세요.")
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
                    mb_d = downloaded / 1024 / 1024
                    mb_t = total / 1024 / 1024
                    print(f"\r    {pct}% ({mb_d:.1f}MB / {mb_t:.1f}MB)", end="", flush=True)
    print(f"\n[+] 저장 완료: {dest}")
    return dest


def main():
    parser = argparse.ArgumentParser(description="Dacon 대회 데이터 다운로드")
    parser.add_argument("--email", help="Dacon 이메일 (자체 가입 계정)")
    parser.add_argument("--password", help="Dacon 비밀번호 (자체 가입 계정)")
    parser.add_argument("--cookie", help="쿠키 문자열 (소셜 로그인 계정)")
    parser.add_argument("--cookie-stdin", action="store_true",
                        help="stdin에서 JSON 쿠키 dict를 읽음 (dacon_auto.py 전용)")
    parser.add_argument("--cpt_id", required=True, help="대회 ID (URL 숫자)")
    parser.add_argument("--output", default=".", help="저장 디렉토리 (기본: 현재 폴더)")
    args = parser.parse_args()

    if not args.cookie_stdin and not args.cookie and not (args.email and args.password):
        print("[!] --cookie-stdin, --cookie, 또는 (--email + --password) 중 하나가 필요합니다.")
        parser.print_help()
        sys.exit(1)

    os.makedirs(args.output, exist_ok=True)
    session = _make_session()

    if args.cookie_stdin:
        raw = sys.stdin.read().strip()
        try:
            cookie_dict = json.loads(raw)
        except json.JSONDecodeError:
            print(f"[!] stdin JSON 파싱 실패: {raw[:80]}")
            sys.exit(1)
        login_cookie_dict(session, cookie_dict)
    elif args.cookie:
        login_cookie(session, args.cookie)
    else:
        login_password(session, args.email, args.password)

    print(f"[+] 대회 데이터 조회 중... (cpt_id={args.cpt_id})")
    link = get_data_link(session, args.cpt_id)
    print(f"[+] 데이터 링크 확인 완료")
    log_download(session, args.cpt_id)
    download_file(session, link, args.output)


if __name__ == "__main__":
    main()
