"""Visible setup stages, bounded child processes and a persistent setup report."""
import json
import os
from pathlib import Path
import queue
import signal
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
REPORT = []


def phase(name, action):
    started = time.monotonic()
    record = {'stage': name, 'status': 'running'}
    REPORT.append(record)
    def save():
        (ROOT / 'tools').mkdir(exist_ok=True)
        temporary = ROOT / 'tools/setup-report.tmp'
        temporary.write_text(json.dumps(REPORT, indent=2), encoding='utf-8')
        temporary.replace(ROOT / 'tools/setup-report.json')
    save()
    print(f'\n>>> {name}', flush=True)
    stop = threading.Event()
    def heartbeat():
        while not stop.wait(10):
            print(f'    {name}: still working ({int(time.monotonic()-started)}s). See logs/tools/setup.log for command output.', flush=True)
    thread = threading.Thread(target=heartbeat, daemon=True)
    thread.start()
    try:
        result = action()
        record['status'] = 'complete'
        return result
    except Exception as error:
        record.update(status='failed', error=str(error))
        raise
    finally:
        stop.set();thread.join()
        record['seconds'] = round(time.monotonic()-started, 1)
        save()
        print(f'<<< {name}: {record["status"]} ({record["seconds"]}s)', flush=True)


def run_command(command, *, cwd, env=None, timeout=1200, idle_timeout=None):
    try:
        from log_paths import tools_log
        log_path = tools_log('setup.log')
    except ImportError:
        log_path = ROOT / 'logs' / 'tools' / 'setup.log'
        log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open('a', encoding='utf-8') as log:
        log.write('\n$ ' + subprocess.list2cmdline(list(map(str, command))) + '\n');log.flush()
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, start_new_session=os.name != 'nt')
        output = queue.Queue(maxsize=256)
        def read():
            try:
                while chunk := process.stdout.read1(4096): output.put(chunk)
            finally: output.put(None)
        thread = threading.Thread(target=read, daemon=True);thread.start()
        started = last_output = last_notice = time.monotonic()
        finished = False
        try:
            while not finished or process.poll() is None:
                now = time.monotonic()
                if idle_timeout and now-last_output > idle_timeout:
                    raise TimeoutError(f'Setup command produced no output for {idle_timeout}s. Re-run Setup.cmd; see logs/tools/setup.log.')
                if now-started > timeout: raise TimeoutError(f'Setup command exceeded {timeout}s. Re-run Setup.cmd; see logs/tools/setup.log.')
                try: chunk = output.get(timeout=.2)
                except queue.Empty: chunk = b''
                if chunk is None: finished = True
                elif chunk:
                    text = chunk.decode('utf-8', 'replace');sys.stdout.write(text);sys.stdout.flush()
                    log.write(text);log.flush();last_output = now
                if now-last_notice >= 10:
                    notice = f'\n    Process active: {int(now-started)}s elapsed; {int(now-last_output)}s since output. Download 100% may still mean extraction/verification.\n'
                    print(notice, end='', flush=True);log.write(notice);log.flush();last_notice=now
            code = process.wait()
            if code: raise subprocess.CalledProcessError(code, command)
        finally:
            if process.poll() is None:
                if os.name == 'nt':
                    subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15)
                else:
                    try: os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError: pass
            process.wait()
            process.stdout.close()
