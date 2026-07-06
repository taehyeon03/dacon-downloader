#!/usr/bin/env python3
"""
노트북 로컬 터미널에서 실행:
  python3 ~/dacon_auto.py 236727

Chrome 쿠키 자동 추출 → SSH로 rtx-5070ti에서 다운로드
"""

import sys
import subprocess
import argparse
import json
import os

G = "\033[32m"   # green
R = "\033[31m"   # red
Y = "\033[33m"   # yellow
B = "\033[1m"    # bold
E = "\033[0m"    # reset


def log(msg, color=G):
    print(f"{color}{B}[+]{E} {msg}")


def err(msg):
    print(f"{R}{B}[!]{E} {msg}", file=sys.stderr)


def ensure_deps():
    for pkg, imp in [("browser-cookie3", "browser_cookie3"), ("secretstorage", "secretstorage")]:
        try:
            __import__(imp)
        except ImportError:
            print(f"{Y}[*]{E} {pkg} 설치 중...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg], check=True)


def get_dacon_cookies():
    import browser_cookie3

    for domain in (".dacon.io", "dacon.io"):
        try:
            jar = browser_cookie3.chrome(domain_name=domain)
            cookies = {c.name: c.value for c in jar}
            if cookies:
                return cookies
        except Exception as e:
            err(f"Chrome 쿠키 읽기 실패: {e}")
            err("Chrome이 완전히 종료된 상태인지, 또는 dacon.io에 로그인되어 있는지 확인하세요.")
            sys.exit(1)

    err("Dacon 쿠키를 찾지 못했습니다.")
    err("Chrome에서 dacon.io에 로그인한 뒤 다시 시도해주세요.")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Dacon 자동 다운로더 (노트북에서 실행)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="예시:\n  python3 ~/dacon_auto.py 236727\n  python3 ~/dacon_auto.py 236727 --output ~/datasets",
    )
    parser.add_argument("cpt_id", help="대회 ID (예: 236727)")
    parser.add_argument("--output", default="~/dacon/data", help="rtx-5070ti 내 저장 경로 (기본: ~/dacon/data)")
    parser.add_argument("--remote", default="rtx-5070ti", help="SSH 호스트명 (기본: rtx-5070ti)")
    args = parser.parse_args()

    ensure_deps()

    log("Chrome에서 Dacon 쿠키 추출 중...")
    cookies = get_dacon_cookies()
    log(f"쿠키 {len(cookies)}개 추출 완료")

    remote_cmd = (
        f"python3 ~/dacon-downloader/dacon_download.py "
        f"--cookie-stdin "
        f"--cpt_id {args.cpt_id} "
        f"--output {args.output}"
    )

    log(f"{args.remote} 에서 다운로드 시작...")
    print()

    result = subprocess.run(
        ["ssh", args.remote, remote_cmd],
        input=json.dumps(cookies).encode(),
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
