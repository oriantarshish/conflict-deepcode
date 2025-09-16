# Conflict DeepCode — Installation and Setup Guide

This guide describes how to install and run Conflict DeepCode on Windows, macOS, and Linux. It also explains prerequisites, full-access mode, increasing the AI context window, and troubleshooting.

If you only need quick start commands, jump to:
- Windows quick start
- macOS quick start
- Linux quick start
- From source (Python) install
- NPM global install

1) Prerequisites

- Node.js 16+ recommended (18+ preferred)
- Python 3.8+
- Ollama installed and running (the installer can auto-install, but manual steps are provided)

2) Install via NPM (recommended cross-platform)

The NPM package provides:
- A cross-platform CLI shim that locates Python and runs the Python CLI
- Automatic Ollama setup attempt on install
- Post-install configuration created at: ~/.conflict-deepcode/config.yaml

Global install:
npm install -g conflict-deepcode

After installation, two commands are available globally:
- dpcd — the chatbox interactive interface
- deepcode — the full CLI

Verifying the install:
deepcode --help
dpcd

3) Install from source (Python)

If you prefer Python-only install (no Node):

- Install Python dependencies:
python -m pip install -r requirements.txt

- Editable install to expose console scripts:
python -m pip install -e .

- Verify entry points:
deepcode --help
dpcd

If deepcode is not found on Windows PowerShell, ensure the Python Scripts directory is on PATH.

4) macOS setup notes

Ollama
- The installer will automatically try to install Ollama using the official script
- If that fails, it will attempt to use Homebrew as a fallback
- Manual installation:
  - Preferred: Homebrew
  brew install ollama

  - Alternative:
  curl -fsSL https://ollama.ai/install.sh | sh

Start the Ollama service:
- If using the app or service is already running, nothing else required
- Otherwise start in background:
nohup ollama serve > /dev/null 2>&1 &

Download the default model:
ollama pull deepseek-coder-v2

Python and Node
- The installer automatically detects Python 3.8+ installations
- It tries python3 first, then python, and verifies the version is 3.8+
- Check versions manually:
python3 --version
node --version

- If Python is only available as python:
python --version

5) Windows setup notes

Ollama
- Download and install from https://ollama.ai
- Run Ollama:
ollama serve

Download the model:
ollama pull deepseek-coder-v2

Python
- On Windows, the launcher py or python should work. If python3 is not present, deepcode will try python or py automatically.

6) Linux setup notes

Ollama
- Script:
curl -fsSL https://ollama.ai/install.sh | sh

Start and enable service (if systemd present):
sudo systemctl start ollama
sudo systemctl enable ollama

Or run it in the background:
nohup ollama serve > /dev/null 2>&1 &

Pull the model:
ollama pull deepseek-coder-v2

7) Running Conflict DeepCode

- Interactive chatbox (recommended):
dpcd

- Full CLI:
deepcode --help

Key commands:
- deepcode chat
- deepcode create <target>
- deepcode modify <file> "<description>"
- deepcode explain <file> [--detail basic|detailed|deep]
- deepcode review <file> [--style security|performance|maintainability|all]
- deepcode test <file> [--framework pytest|jest]
- deepcode status
- deepcode init

Full file-ops CLI (added for demos and power users):
- Delete a file safely (backup by default):
deepcode delete <file> [--force]

- Clear a file’s content (backup by default):
deepcode clear <file> [--force]

- Run a file using the appropriate runtime:
deepcode run <file> [args...]

- Append content to a file:
deepcode append <file> --text "some text"
deepcode append <file> --from-file ./snippet.txt

- Move/rename a file (with optional backup at source and overwrite):
deepcode mv <src> <dst> [--overwrite] [--no-backup]

- Copy a file:
deepcode cp <src> <dst> [--overwrite]

- Create a directory (recursive):
deepcode mkdir <dir>

- Remove a directory:
deepcode rmdir <dir> [--recursive] [--force]

Important safety behavior:
- By default, dangerous operations prompt/backup unless overridden
- Backups are stored under:
~/.conflict-deepcode/backups

8) Full-access/unsafe mode

To grant the agent broad file-operation ability without confirmations (use with care):
- Temporary: add --unsafe to your CLI session:
deepcode --unsafe chat
deepcode --unsafe delete <file>

- Persistent (in config):
~/.conflict-deepcode/config.yaml
agent:
  enable_dangerous_action_confirmation: false

Warning: Unsafe mode can delete/clear files without prompting. Use only when you are confident and ideally under version control.

9) Increasing the AI context window (larger prompts)

You can change model context (num_ctx) and generation length (num_predict):

- Temporary overrides via CLI:
deepcode --num-ctx 32768 --num-predict 2048 chat

- Persistent via config file:
~/.conflict-deepcode/config.yaml
ollama:
  host: http://localhost:11434
  model: deepseek-coder-v2
  timeout: 120
  num_ctx: 32768
  num_predict: 2048
  temperature: 0.2
  top_p: 0.9

Related project settings (bigger files/context):
project:
  max_file_size: 5MB
  context_lines: 100

10) Configuration file location

Global config:
~/.conflict-deepcode/config.yaml

Local (per-project) initialization:
deepcode init
Creates .deepcode/config.yaml with project-specific ignores and settings.

11) Troubleshooting

- deepcode says Ollama not running:
Ensure ollama serve is running locally and the default host is reachable:
curl http://localhost:11434/api/version

- Model deepseek-coder-v2 not found:
Run:
ollama pull deepseek-coder-v2

- Python not found:
Install Python 3.8+ from https://python.org. The installer automatically detects Python installations across platforms:
- On Windows: tries python, then py
- On macOS/Linux: tries python3, then python, and verifies version is 3.8+

- Node not found:
Install Node.js from https://nodejs.org

- Permissions issues (macOS/Linux):
Use a Python virtualenv or ensure your PATH and permissions are configured. For NPM global installs, using a Node version manager (nvm) is recommended.

- Path issues (Windows):
Confirm that the Python Scripts directory and npm global bin directory are on PATH.

- Terminal UI fails to launch:
Try:
deepcode chat
or
dpcd

12) Uninstall

- NPM global uninstall:
npm uninstall -g conflict-deepcode

- Python uninstall (editable install):
pip uninstall deepcode-ai

Backups and user config remain in:
~/.conflict-deepcode
Remove manually if you wish:
rm -rf ~/.conflict-deepcode   # macOS/Linux
rmdir /S /Q %USERPROFILE%\.conflict-deepcode  # Windows Command Prompt