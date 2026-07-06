#!/usr/bin/env python3
"""
로컬 노트북에서 실행:
  python3 dacon_auto.py --cpt_id 236727

Chrome 쿠키 자동 추출 → SSH로 rtx-5070ti에서 다운로드 실행
"""

import sys
import subprocess
import argparse
import json
import os


def ensure_deps():
    for pkg in ("browser-cookie3", "secretstorage"):
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            print(f"[*] {pkg} 설치 중...")
            subprocess.run([sys.executable, "-m", "pip", "install", pkg], check=True)


def get_dacon_cookies():
    import browser_cookie3

    for domain in (".dacon.io", "dacon.io"):
        jar = browser_cookie3.chrome(domain_name=domain)
        cookies = {c.name: c.value for c in jar}
        if cookies:
            return cookies

    print("[!] Dacon 쿠키 없음. Chrome에서 dacon.io 로그인 상태인지 확인하세요.")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Dacon 자동 다운로더 (노트북에서 실행)")
    parser.add_argument("--cpt_id", required=True, help="대회 ID (URL 숫자)")
    parser.add_argument("--output", default="~/dacon/data", help="rtx-5070ti 내 저장 경로")
    parser.add_argument("--remote", default="rtx-5070ti", help="SSH 호스트명 (기본: rtx-5070ti)")
    args = parser.parse_args()

    ensure_deps()

    print("[+] Chrome에서 Dacon 쿠키 추출 중...")
    cookies = get_dacon_cookies()
    cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
    print(f"[+] 쿠키 {len(cookies)}개 추출 완료")

    # 쿠키를 JSON으로 원격 전달 (따옴표 이스케이프 문제 방지)
    cookie_json = json.dumps(cookie_str)

    remote_cmd = (
        f"python3 ~/dacon-downloader/dacon_download.py "
        f"--cookie {cookie_json} "
        f"--cpt_id {args.cpt_id} "
        f"--output {args.output}"
    )

    print(f"[+] {args.remote} 에서 다운로드 시작...\n")
    result = subprocess.run(["ssh", args.remote, remote_cmd])
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
