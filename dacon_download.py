#!/usr/bin/env python3
"""
Dacon 대회 데이터 다운로드 스크립트
Usage: python3 dacon_download.py --email EMAIL --password PW --cpt_id 대회ID [--output DIR]
cpt_id: 대회 URL의 숫자 (https://dacon.io/competitions/official/235900/ → 235900)
"""

import argparse
import os
import sys
import requests
from pathlib import Path
from urllib.parse import urlparse

API = "https://newapi.dacon.io"

def login(session, email, password):
    resp = session.post(f"{API}/login/self_login", json={
        "mail": email,
        "password": password,
        "returnTo": "/",
        "locale": "ko",
    })
    data = resp.json()
    if resp.status_code != 200 or data.get("message") not in ("ok", None):
        print(f"[!] 로그인 실패: {data}")
        sys.exit(1)
    print(f"[+] 로그인 성공")
    return session

def get_data_link(session, cpt_id):
    resp = session.get(f"{API}/competition/data?cpt_id={cpt_id}")
    data = resp.json()
    link = data.get("data", {}).get("data_link") or data.get("data_link")
    if not link or link == "null":
        # Try alternate key
        for v in data.values():
            if isinstance(v, dict):
                link = v.get("data_link")
                if link and link != "null":
                    break
    if not link or link == "null":
        print(f"[!] 데이터 링크 없음. 대회 참가 후 시도해주세요.")
        print(f"    응답: {data}")
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
    parser.add_argument("--email", required=True, help="Dacon 이메일")
    parser.add_argument("--password", required=True, help="Dacon 비밀번호")
    parser.add_argument("--cpt_id", required=True, help="대회 ID (URL 숫자)")
    parser.add_argument("--output", default=".", help="저장 디렉토리 (기본: 현재 폴더)")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0", "Referer": "https://dacon.io/"})

    login(session, args.email, args.password)
    print(f"[+] 대회 데이터 정보 조회 중... (cpt_id={args.cpt_id})")
    link = get_data_link(session, args.cpt_id)
    print(f"[+] 데이터 링크: {link}")
    log_download(session, args.cpt_id)
    download_file(session, link, args.output)

if __name__ == "__main__":
    main()
