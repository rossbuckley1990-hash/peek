# Install peek (instructions for AI agents)

The user wants you to install **peek**, a read-only CLI that lets you read their other
terminal tabs (dev servers, test watchers, builds, logs) so they don't have to copy-paste
output to you. Follow these steps, then tell the user what happened in two or three sentences.

## 1. Already installed?

Run `peek --version`. If it prints a version, run the install command in step 2 anyway to upgrade,
then continue.

## 2. Install the CLI

Use the first option that works. Don't use `sudo`. Don't install `peek` from PyPI (that name
belongs to an unrelated package).

```bash
uv tool install --force git+https://github.com/rossbuckley1990-hash/peek
```

```bash
pipx install --force git+https://github.com/rossbuckley1990-hash/peek
```

If neither `uv` nor `pipx` exists, use the single-file install (needs `python3` 3.9 or newer):

```bash
mkdir -p ~/.local/bin && curl -fsSL https://raw.githubusercontent.com/rossbuckley1990-hash/peek/main/peek.py -o ~/.local/bin/peek && chmod +x ~/.local/bin/peek
```

If `peek` then isn't found, `~/.local/bin` isn't on PATH. Tell the user and offer to add it to their shell profile.

## 3. Teach your agents to use it

```bash
peek skill --install
```

This writes a `SKILL.md` for every agent it finds (Claude Code, Codex, Gemini CLI, Cursor, OpenClaw,
`~/.agents`). It only touches folders that already exist.

If you are an agent without skills support (Aider, Copilot, …): ask the user before appending
the output of `peek skill` to the project's `AGENTS.md`.

## 4. Check it works

```bash
peek doctor
```

- **macOS permission prompt:** the first time, macOS may ask whether your app may control
  "Terminal" (or "iTerm2"). Tell the user to click **OK**. That's how peek reads tab text. If doctor
  says access is blocked: System Settings > Privacy & Security > Automation.
- **Sandboxed agents (e.g. Codex):** peek talks to the terminal app and reads the process list.
  If your sandbox blocks that, ask the user to let `peek` run outside the sandbox.
- **No readable terminals?** Fine. It just means nothing's open yet.

## 5. Tell the user

Say, in your own words:

- peek is installed and which terminals it can see (from `peek doctor`).
- From now on they can just say things like *"the page is broken"*, *"tests are failing"* or
  *"check my terminal"*, and you'll read their terminals yourself instead of asking for pastes.
- Terminals peek can read directly: Terminal.app, iTerm2, tmux, WezTerm, kitty. For VS Code,
  Cursor, Ghostty or Warp terminals, start the command as `peek run -- npm run dev` (it runs exactly
  the same, and peek can read it).

Uninstall later with `peek skill --uninstall`, then `uv tool uninstall agent-peek` (or pipx), and `rm -rf ~/.peek`.
