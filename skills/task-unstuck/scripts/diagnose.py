#!/usr/bin/env python3
"""막혔을 때 현재 상태를 한 화면으로 모은다 (표준 라이브러리만).

사용법: python3 diagnose.py [--port 3000]
보는 것: git 최근 커밋과 바뀐 파일, 열려 있는 포트와 바인딩 주소, 포트 응답,
서버로 보이는 프로세스, 최근 수정 파일, 파이썬·노드 버전, 디스크 여유.
아무것도 고치지 않는다.
"""
import argparse
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

SKIP_DIRS = {".git", ".harness", "node_modules", ".agents", ".claude", ".codex",
             ".cache", ".config", ".local", ".npm", "__pycache__", ".pytest_cache", ".venv", "venv"}
SERVER_HINTS = ("http.server", "flask", "uvicorn", "gunicorn", "streamlit", "vite",
                "next dev", "next start", "npm run dev", "npm start", "runserver",
                "server.py", "server.js", "app.py", "main.py", "index.js")
NOT_SERVER = ("codex", "claude", "diagnose.py", "ccr-ca")


def run(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return (out.stdout or out.stderr).strip()
    except Exception as e:  # 명령이 없거나 멈추면 이유만 보여 준다
        return f"(실행 못 함: {e.__class__.__name__})"


def section(title):
    print(f"\n== {title}")


def git_info():
    section("git")
    if not shutil.which("git"):
        print("  git 없음")
        return
    inside = run(["git", "rev-parse", "--is-inside-work-tree"])
    if inside != "true":
        print("  git 저장소 아님 (커밋으로 되돌릴 수 없음)")
        return
    print("  최근 커밋:")
    for line in run(["git", "log", "--oneline", "-5"]).splitlines():
        print("   ", line)
    changed = run(["git", "status", "--short"]).splitlines()
    print(f"  커밋 안 된 변경 {len(changed)}개" + (":" if changed else ""))
    for line in changed[:15]:
        print("   ", line)
    if len(changed) > 15:
        print(f"    ... 외 {len(changed) - 15}개")


def _hex_ip4(h):
    b = bytes.fromhex(h)
    return ".".join(str(x) for x in b[::-1])


def _hex_ip6(h):
    if h == "0" * 32:
        return "::"
    if h == "00000000000000000000000001000000":
        return "::1"
    if h.startswith("0000000000000000FFFF0000"):
        return "::ffff:" + _hex_ip4(h[24:])
    return "ipv6"


def listening_ports():
    found, readable = [], False
    for path, conv in (("/proc/net/tcp", _hex_ip4), ("/proc/net/tcp6", _hex_ip6)):
        try:
            with open(path) as f:
                next(f)
                readable = True
                for line in f:
                    parts = line.split()
                    if len(parts) > 3 and parts[3] == "0A":  # LISTEN
                        addr, port = parts[1].split(":")
                        found.append((conv(addr), int(port, 16)))
        except (OSError, ValueError, StopIteration):
            continue  # IPv6가 꺼진 환경 등은 건너뛴다
    if not readable:
        return None
    return sorted(set(found), key=lambda x: (x[1], x[0]))


def _bind_note(addr):
    if addr in ("127.0.0.1", "::1"):
        return "  ← 로컬 전용이라 미리보기가 못 본다. 0.0.0.0으로 띄울 것"
    if addr in ("0.0.0.0", "::"):
        return "  (모든 주소, 미리보기 가능)"
    return ""


def port_info(port):
    section(f"포트 (미리보기 기본 {port})")
    ports = listening_ports()
    if ports is None:
        print("  /proc를 읽을 수 없는 환경이라 연결 시험만 한다")
    else:
        target = [(a, p) for a, p in ports if p == port]
        for addr, p in target:
            print(f"  {addr}:{p}{_bind_note(addr)}")
        if not target:
            print(f"  {port}번은 안 열려 있음 (서버가 안 떠 있거나 다른 포트)")
            dev = [(a, p) for a, p in ports
                   if 3000 <= p < 4000 or 5000 <= p < 6000 or 8000 <= p < 9000]
            for addr, p in dev:
                print(f"  대신 열린 포트 {addr}:{p}{_bind_note(addr)}"
                      f" → 내 서버라면 미리보기 PORT를 {p}로 바꾸거나 서버를 {port}으로 띄울 것")
        others = [f"{a}:{p}" for a, p in ports if p != port]
        if others:
            print("  그 밖에 열린 포트(환경 것일 수 있음): " + ", ".join(others[:8]))
    section(f"{port}번 응답")
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=3) as r:
            body = r.read(300).decode("utf-8", "replace").replace("\n", " ")
            print(f"  HTTP {r.status} · {body[:120]}")
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} (서버는 떠 있지만 / 경로가 오류. 경로를 확인)")
    except Exception as e:
        print(f"  응답 없음: {e.__class__.__name__} {getattr(e, 'reason', '') or e}")


def server_processes():
    section("서버로 보이는 프로세스")
    if not os.path.isdir("/proc"):
        print("  (확인 못 함)")
        return
    me = os.getpid()
    hits = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit() or int(pid) == me:
            continue
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                cmd = f.read().replace(b"\0", b" ").decode("utf-8", "replace").strip()
        except OSError:
            continue
        low = cmd.lower()
        if cmd and not any(n in low for n in NOT_SERVER) and any(h in low for h in SERVER_HINTS):
            hits.append((pid, cmd[:110]))
    if not hits:
        print("  없음")
    for pid, cmd in hits[:8]:
        print(f"  pid {pid}: {cmd}")


def recent_files(root, limit=8):
    section("최근 수정 파일")
    items = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        if dirpath.count(os.sep) - root.count(os.sep) > 3:
            dirnames[:] = []
        for name in filenames:
            p = os.path.join(dirpath, name)
            try:
                items.append((os.path.getmtime(p), p))
            except OSError:
                pass
    now = time.time()
    for mt, p in sorted(items, reverse=True)[:limit]:
        mins = int((now - mt) // 60)
        print(f"  {mins:>4}분 전  {os.path.relpath(p, root)}")


def env_info(root):
    section("환경")
    print(f"  {platform.system()} · Python {platform.python_version()} · 작업 폴더 {root}")
    node = shutil.which("node")
    print("  node " + (run(["node", "--version"]) if node else "없음"))
    pip_has = []
    for mod in ("pytest", "flask", "fastapi", "uvicorn", "pandas", "streamlit"):
        try:
            __import__(mod)
            pip_has.append(mod)
        except Exception:
            pass
    print("  설치된 주요 파이썬 패키지: " + (", ".join(pip_has) if pip_has else "없음 (표준 라이브러리만)"))
    du = shutil.disk_usage(root)
    print(f"  디스크 여유 {du.free // (1024 * 1024)} MB")


def main():
    ap = argparse.ArgumentParser(description="막혔을 때 상태 모으기")
    ap.add_argument("--port", type=int, default=3000)
    args = ap.parse_args()
    root = os.getcwd()
    print(f"[진단] {time.strftime('%H:%M:%S')}")
    git_info()
    port_info(args.port)
    server_processes()
    recent_files(root)
    env_info(root)
    print("\n다음: 마지막으로 실패한 명령을 한 번만 다시 실행해 오류 원문을 확보한다.")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
