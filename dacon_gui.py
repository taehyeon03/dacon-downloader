#!/usr/bin/env python3
"""
Dacon GUI 데이터 다운로더
- 브라우저 창에서 로그인 (Google/카카오 모두 가능)
- 로그인 완료 시 쿠키 자동 캡처 → 다운로드
"""

import sys
import os
import subprocess
import threading
import requests
from pathlib import Path
from urllib.parse import urlparse

# Wayland 세션에서 DISPLAY가 없을 때 XWayland 디스플레이 자동 설정
if not os.environ.get("DISPLAY"):
    import glob
    socks = glob.glob("/tmp/.X11-unix/X*")
    if socks:
        num = socks[0].replace("/tmp/.X11-unix/X", "")
        os.environ["DISPLAY"] = f":{num}"
    else:
        os.environ["DISPLAY"] = ":0"

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

API = "https://newapi.dacon.io"


def ensure_playwright():
    try:
        import playwright  # noqa
    except ImportError:
        print("playwright 설치 중...", flush=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium", "--with-deps"], check=True)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dacon 데이터 다운로더")
        self.resizable(False, False)
        self._build()

    def _build(self):
        pad = {"padx": 20, "pady": 6}
        f = ttk.Frame(self, padding=(24, 18))
        f.pack(fill=tk.BOTH, expand=True)

        ttk.Label(f, text="Dacon 데이터 다운로더", font=("", 15, "bold")).pack(**pad)
        ttk.Separator(f).pack(fill=tk.X, padx=20, pady=4)

        # cpt_id
        ttk.Label(f, text="대회 ID  (예: dacon.io/competitions/official/235900/ → 235900)").pack(anchor=tk.W, padx=20)
        self.cpt_var = tk.StringVar()
        ttk.Entry(f, textvariable=self.cpt_var, width=46, font=("", 11)).pack(padx=20, pady=(2, 8), fill=tk.X)

        # output folder
        ttk.Label(f, text="저장 폴더").pack(anchor=tk.W, padx=20)
        row = ttk.Frame(f)
        row.pack(padx=20, pady=(2, 8), fill=tk.X)
        self.out_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        ttk.Entry(row, textvariable=self.out_var, font=("", 10)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(row, text="찾아보기", command=self._browse).pack(side=tk.RIGHT, padx=(6, 0))

        ttk.Separator(f).pack(fill=tk.X, padx=20, pady=6)

        # button
        self.btn = ttk.Button(f, text="  🌐  브라우저 열고 로그인 & 다운로드  ", command=self._start)
        self.btn.pack(pady=4)

        # progress
        self.prog_label = ttk.Label(f, text="")
        self.prog_label.pack()
        self.prog = ttk.Progressbar(f, length=420, mode="determinate")
        self.prog.pack(padx=20, pady=(2, 8))

        # log
        ttk.Label(f, text="로그").pack(anchor=tk.W, padx=20)
        self.log = tk.Text(f, height=9, state=tk.DISABLED, wrap=tk.WORD,
                           bg="#1e1e1e", fg="#d4d4d4", font=("monospace", 9))
        self.log.pack(padx=20, pady=(2, 10), fill=tk.BOTH, expand=True)

    def _browse(self):
        d = filedialog.askdirectory()
        if d:
            self.out_var.set(d)

    def _log(self, msg, *, replace_last=False):
        self.log.configure(state=tk.NORMAL)
        if replace_last:
            self.log.delete("end-2l linestart", "end-1l lineend+1c")
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)
        self.update()

    def _set_prog(self, pct, label=""):
        self.prog["value"] = pct
        self.prog_label.configure(text=label)
        self.update()

    def _start(self):
        cpt_id = self.cpt_var.get().strip()
        output = self.out_var.get().strip() or "."
        if not cpt_id:
            messagebox.showerror("오류", "대회 ID를 입력해주세요.")
            return
        self.btn.configure(state=tk.DISABLED)
        self.log.configure(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.configure(state=tk.DISABLED)
        self._set_prog(0)
        threading.Thread(target=self._run, args=(cpt_id, output), daemon=True).start()

    def _run(self, cpt_id, output):
        try:
            os.makedirs(output, exist_ok=True)
            self._log("브라우저를 열겠습니다. Dacon에 로그인해주세요...")
            self._log("Google / 카카오 로그인 모두 가능합니다.")

            cookies = self._browser_login()
            session = self._make_session(cookies)

            # 로그인 확인
            resp = session.get(f"{API}/myinfo/profile")
            info = resp.json()
            name = (info.get("data") or {}).get("name", "")
            if not name:
                raise Exception(f"로그인 확인 실패. 쿠키 문제일 수 있습니다.\n응답: {info}")
            self._log(f"✓ 로그인 확인: {name}")
            self._set_prog(10, "로그인 완료")

            # 데이터 링크 조회
            self._log(f"데이터 링크 조회 중... (cpt_id={cpt_id})")
            link = self._get_link(session, cpt_id)
            self._log(f"✓ 데이터 링크: {link[:60]}...")
            self._set_prog(20, "링크 확인 완료")

            # 다운로드 로그 기록
            session.post(f"{API}/competition/download", json={"cpt_id": cpt_id})

            # 다운로드
            dest = self._download(session, link, output)
            self._set_prog(100, "완료!")
            self._log(f"✓ 저장 완료: {dest}")
            messagebox.showinfo("완료", f"다운로드 완료!\n\n{dest}")
        except Exception as e:
            self._log(f"✗ 오류: {e}")
            messagebox.showerror("오류", str(e))
        finally:
            self.btn.configure(state=tk.NORMAL)

    def _browser_login(self):
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, args=["--start-maximized"])
            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            page.goto("https://dacon.io/login")

            self._log("→ 로그인 완료 후 자동으로 창이 닫힙니다.")

            # 로그인 완료 감지: /login 에서 벗어나고 쿠키가 설정될 때까지 대기
            page.wait_for_function(
                """() => {
                    const url = window.location.href;
                    return !url.includes('/login') && !url.includes('/callback') && !url.includes('/oauth');
                }""",
                timeout=180_000,
            )
            page.wait_for_timeout(2000)

            cookies = context.cookies()
            browser.close()
            self._log("브라우저 닫힘. 쿠키 수집 완료.")
            return cookies

    def _make_session(self, cookies):
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Referer": "https://dacon.io/",
            "Origin": "https://dacon.io",
        })
        for c in cookies:
            domain = c.get("domain", "").lstrip(".")
            if "dacon.io" in domain:
                session.cookies.set(c["name"], c["value"], domain=domain)
        return session

    def _get_link(self, session, cpt_id):
        resp = session.get(f"{API}/competition/data?cpt_id={cpt_id}")
        data = resp.json()
        link = None
        if isinstance(data.get("data"), dict):
            link = data["data"].get("data_link")
        if not link:
            link = data.get("data_link")
        if not link or link == "null":
            raise Exception(f"데이터 링크 없음. 대회 참가 후 시도해주세요.\n응답: {data}")
        return link

    def _download(self, session, url, output_dir):
        filename = urlparse(url).path.split("/")[-1]
        dest = Path(output_dir) / filename
        self._log(f"다운로드 시작: {filename}")
        with session.get(url, stream=True) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = 20 + int(downloaded / total * 80)
                        mb_d = downloaded / 1024 / 1024
                        mb_t = total / 1024 / 1024
                        self._set_prog(pct, f"{mb_d:.1f} MB / {mb_t:.1f} MB")
        return dest


if __name__ == "__main__":
    ensure_playwright()
    app = App()
    app.mainloop()
