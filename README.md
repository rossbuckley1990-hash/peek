<h1 align="center">👀 peek</h1>

<p align="center">
  <strong>Give your AI agent eyes on your other terminals.</strong><br>
  Stop copy-pasting errors into Claude Code, Codex, Cursor, Gemini CLI or any other agent.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT"></a>
  <img src="https://img.shields.io/badge/python-3.9+-green.svg" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/dependencies-zero-brightgreen.svg" alt="zero dependencies">
  <img src="https://img.shields.io/badge/macOS%20%C2%B7%20Linux-supported-lightgrey.svg" alt="macOS and Linux">
</p>

---

Your dev server, test watcher, build and logs run in **other terminal tabs**. Your agent can't
see them. So every bug turns into this:

> **You:** the cart page is broken<br>
> **Agent:** Could you paste the error from your terminal?<br>
> **You:** *switch tab, scroll up, select, copy, switch back, paste*<br>
> **Agent:** Fixed! 🎉<br>
> **You:** *switch tab* …it's still broken.

**peek** lets the agent read those tabs itself. It works on the terminals you already have open,
including output printed before peek was installed. You don't restart anything, wrap anything or
configure anything.

> **You:** the cart page is broken<br>
> **Agent:** *runs `peek errors`* → finds `ReferenceError: settings is not defined` at `server.js:11` in your `npm run dev` tab → fixes it → *runs `peek 2 --wait`* → sees your server reload cleanly → *requests `/cart` again* → no error. **Verified against your real, running server.**

That loop isn't a mock-up. It's what a fresh agent did on its first try, with nothing but peek's skill file and that one-line complaint.

## Install: paste this to your agent

```
Install peek: https://raw.githubusercontent.com/rossbuckley1990-hash/peek/main/install.md
```

Your agent installs the CLI, teaches itself (and your other agents) how to use it, and checks it can
see your terminals. That's it. Upgrading uses the same sentence.

<details>
<summary>Or install it yourself</summary>

```bash
uv tool install git+https://github.com/rossbuckley1990-hash/peek && peek skill --install
```

or `pipx install git+https://github.com/rossbuckley1990-hash/peek`, or grab the single file:
`curl -fsSL https://raw.githubusercontent.com/rossbuckley1990-hash/peek/main/peek.py -o ~/.local/bin/peek && chmod +x ~/.local/bin/peek`

`peek skill --install` drops a `SKILL.md` into every agent it finds: Claude Code, Codex, Gemini
CLI, Cursor, OpenClaw and `~/.agents`. For agents without skills, paste `peek skill` into `AGENTS.md`.
</details>

## Then just talk normally

| You say | Your agent |
|---|---|
| "the page is broken" | `peek errors` → reads the stack trace from your dev server, fixes it, `peek 1 --wait` to watch it reload |
| "tests are failing" | reads the failing test's assertion straight from your watcher or your last `pytest` run |
| "why won't it start?" | spots `EADDRINUSE`, a missing module or a bad env var in the crashed server's output |
| "check the logs" | reads your `tail -f` / `docker compose logs` tab, with the latest errors first |
| "did that fix it?" | `peek 1 --new` shows only what printed since it last looked |

## What it looks like

```
$ peek
1  npm run dev             ~/shop        :3000  Terminal ttys001
   ✗ TypeError: Cannot read properties of undefined (reading 'reduce')   (9 lines up)
2  zsh (idle)              ~/shop               tmux ttys005
   $ pytest -q  ->  ✗ AssertionError: 100 != 95   (7 lines up)
3  tail -f logs/app.log    ~/shop               tmux ttys012
   ✗ 12:01:07 ERROR payment webhook failed: connect ECONNREFUSED 127.0.0.1:6379
4  claude (this agent)     ~/shop               Terminal ttys000

peek <n> reads one  ·  peek errors shows every error  ·  peek <n> --wait after an edit
```

```
$ peek errors
Start with 1 (npm run dev): Error: Cannot find module './carts'

── 1 · npm run dev · ~/shop · :3000 down · this project ──
   Error: Cannot find module './carts'
   Require stack:
   - ./server.js
       … 8 library frames
       at Object.<anonymous> (./server.js:2:23)
   Failed running 'server.js'. Waiting for file changes before restarting...
   ✗ Error: Cannot find module './carts'   (21 lines from the bottom)

── 3 · tail -f logs/app.log · ~/shop · this project ──
   12:01:07 ERROR payment webhook failed: connect ECONNREFUSED 127.0.0.1:6379
   ✗ 12:01:07 ERROR payment webhook failed: connect ECONNREFUSED 127.0.0.1:6379   (2 lines from the bottom)

2 of 4 terminals with errors. Full output: peek <n>  ·  after you fix it: peek <n> --wait
```

The crashed server comes first. Its port shows as `down`, paths are relative to the project,
library frames are folded, and the same error in two tabs is shown once.

```
$ peek 1 --wait
── 1 · npm run dev · ~/shop · :3000 · lines 9-11 of 11 ──
Change detected in '/Users/you/shop/server.js'
Restarting 'server.js'
shop listening on http://localhost:3000
── the screen was cleared since you last looked (a restart?); showing from the latest restart ·
   ✓ restarted with no errors, but nothing has run the fixed code yet. If the bug happens on a
   request or action, trigger it again (e.g. curl localhost:3000/…, or ask the user to retry),
   then check with `peek 1 --new` ──
```

peek is honest about what it saw. A clean restart is reported as a clean restart, not as "fixed".
In testing, that one line was the difference between an agent saying "fixed" too early and an
agent that curled the page, checked `peek 1 --new`, and *then* said "fixed".

## Commands

| | |
|---|---|
| `peek` | Every terminal: what's running, folder, ports, plus the latest error or last line |
| `peek errors` | Stack traces, failed tests and compile errors from all terminals, this project's first |
| `peek <n\|text>` | Last 80 lines of one terminal. Text matches command, folder, port or title: `peek 3000`, `peek pytest`, `peek server` |
| `peek <n> --wait [regex]` | What it printed since you last looked, waiting up to 30s if nothing yet. Made for "I just saved a file" |
| `peek <n> --new` | Only output since you last looked |
| `peek <n> --last` | Only the last command's output, in an idle shell |
| `peek run -- <cmd>` | Run a command so peek can read it in *any* terminal (VS Code, Cursor, Ghostty, Warp…) |
| `peek doctor` | What peek can see, and what to fix |
| `peek skill --install` | Teach your agents to use peek |

Options: `-n 300` · `--json` · `--raw` (don't mask secrets) · `--timeout 60`

## Which terminals

| Terminal | What peek reads | Status |
|---|---|---|
| **Terminal.app** (macOS) | full scrollback | ✅ tested |
| **tmux** (any OS) | full scrollback | ✅ tested, in CI |
| **iTerm2** | visible screen (its scripting API stops there) | 🧪 built on the documented API, needs real-world reports |
| **WezTerm** | full scrollback | 🧪 built on `wezterm cli`, needs reports |
| **kitty** | full scrollback, with `allow_remote_control yes` | 🧪 built on `kitty @`, needs reports |
| **Ghostty** | lists tabs; Ghostty's AppleScript can't share text yet | ➡️ use `peek run` or tmux |
| **VS Code, Cursor, Warp, anything else** | everything, via `peek run -- npm run dev` | ✅ tested |

Windows: use WSL with tmux, or `peek run`.

## Safe by design

- **Read-only.** peek never types into, sends keys to, or controls a terminal.
- **Local.** No network, no telemetry, no account. One Python file you can read in 15 minutes.
- **Secrets masked by default.** API keys, tokens, `postgres://user:pass@`, `Bearer …` and `KEY=value`
  come out as `sk_l…[redacted]` before your agent ever sees them.
- **Prompt-injection aware.** The skill tells agents that terminal output is data, never instructions.
- **Your agent's own tab is excluded**, so it doesn't read itself.
- On macOS, the first run may ask "*… wants to control Terminal*". That permission is how peek reads tab text.

## Why not just…

**…let the agent run the dev server?** You want it in *your* terminal, where you can watch it,
restart it and keep it running after the agent session ends. It's usually already running anyway. peek
works with what's open right now.

**…use `tmux capture-pane`?** peek uses it. It also reads Terminal.app, iTerm2, WezTerm and kitty,
finds the errors in all of them, remembers what the agent already saw, and waits for the reload
after an edit.

**…use an MCP server?** peek is a plain CLI, so it works in every agent that has a shell, with no config and no
background process. Sandboxed agents just need `peek` allowed.

**…use a logging wrapper?** Wrappers need you to restart your server through them, before the bug happens.
peek reads what's already there. (`peek run` is the wrapper, for terminals that can't be read.)

## How it works

- **Terminal.app / iTerm2:** JavaScript for Automation (`history` / `contents` of each tab)
- **tmux / WezTerm / kitty:** `capture-pane` / `wezterm cli get-text` / `kitty @ get-text`
- **What's running where:** `ps` (the foreground process group of each tab's tty) and `lsof` (ports, folders)
- **Errors:** about 30 patterns tuned on real output from Node, Next.js, Vite, tsc, pytest, unittest,
  Jest, Vitest, Rust, Go, Rails, Django, Docker, npm, Swift, Java, PHP and ESLint, with a test suite
  of false positives (`0 errors`, `error.tsx`, `git log` lines…)
- **"New since you last looked":** an anchor on the last lines seen, kept per agent session. It survives
  dev servers that clear the screen on restart by starting at the latest restart sequence.
- **Ports:** remembered per terminal, so a server that crashed shows `:3000 down` instead of nothing.

## How it was tested

Real processes in real terminals: a Node server under `node --watch` in Terminal.app, tmux panes running
unittest and `tail -f`, and `peek run` under a real tty with Ctrl-C. After each round, a **fresh agent
with no context** got just the skill file and a one-line complaint ("the cart page is broken",
"my shop won't start anymore"). Both fixed the bug using peek alone. Their critiques drove most of
v0.1: honest verdicts, per-session state, error ranking, folded stack frames, and the screen-clear
handling. 44 unit and integration tests, run in CI on macOS and Linux.

One file, standard library only, Python 3.9+. Tests: `python3 -m unittest discover -s tests`.

## Uninstall

```bash
peek skill --uninstall && uv tool uninstall agent-peek && rm -rf ~/.peek
```

## License

MIT
