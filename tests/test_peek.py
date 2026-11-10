"""Tests for peek. Run: python3 -m unittest discover -s tests -v"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import peek  # noqa: E402


def L(s):
    return textwrap.dedent(s).strip("\n").split("\n")


def headline(text):
    lines = L(text)
    blocks = peek.find_errors(lines)
    if not blocks:
        return None
    return lines[peek.best_headline(lines, blocks)].strip()


# --------------------------------------------------------------------------- errors

TRUE_POSITIVES = {
    "node crash": ("""
        shop listening on http://localhost:3457
        /Users/me/shop/cart.js:2
          return cart.lineItems.reduce((sum, item) => sum + item.price, 0);
                                ^
        TypeError: Cannot read properties of undefined (reading 'reduce')
            at cartTotal (/Users/me/shop/cart.js:2:25)
            at Server.<anonymous> (/Users/me/shop/server.js:11:70)

        Node.js v26.12.0
        Failed running 'server.js'. Waiting for file changes before restarting...
        """, "TypeError: Cannot read properties of undefined (reading 'reduce')"),
    "python unittest": ("""
        test_no_discount (test_cart.TestCart.test_no_discount) ... FAIL
        ======================================================================
        FAIL: test_no_discount (test_cart.TestCart.test_no_discount)
        ----------------------------------------------------------------------
        Traceback (most recent call last):
          File "/Users/me/shop/test_cart.py", line 10, in test_no_discount
            self.assertEqual(apply_discount(100, "BOGUS"), 95)
        AssertionError: 100 != 95

        ----------------------------------------------------------------------
        Ran 3 tests in 0.001s

        FAILED (failures=1)
        """, "AssertionError: 100 != 95"),
    "pytest": ("""
        tests/test_cart.py .F.                                                   [100%]
        =================================== FAILURES ===================================
        ________________________________ test_discount _________________________________

            def test_discount():
        >       assert apply_discount(100, "SAVE10") == 95
        E       assert 90.0 == 95

        tests/test_cart.py:8: AssertionError
        =========================== short test summary info ============================
        FAILED tests/test_cart.py::test_discount - assert 90.0 == 95
        ========================= 1 failed, 2 passed in 0.03s ==========================
        """, "tests/test_cart.py:8: AssertionError"),
    "next.js type error": ("""
         ✓ Ready in 1.2s
         ○ Compiling /cart ...
         ⨯ ./app/cart/page.tsx:12:7
        Type error: Property 'lineItems' does not exist on type 'Cart'.
        """, "Type error: Property 'lineItems' does not exist on type 'Cart'."),
    "next.js runtime 500": ("""
         ✓ Compiled /cart in 312ms
         ⨯ TypeError: Cannot read properties of undefined (reading 'map')
            at CartPage (./app/cart/page.tsx:14:24)
         GET /cart 500 in 340ms
        """, "⨯ TypeError: Cannot read properties of undefined (reading 'map')"),
    "vite": ("""
          VITE v7.1.0  ready in 312 ms

          ➜  Local:   http://localhost:5173/
        3:04:11 PM [vite] Internal server error: Failed to resolve import "./Cart" from "src/App.tsx". Does the file exist?
          Plugin: vite:import-analysis
          File: /Users/me/shop/src/App.tsx:3:17
        """, '3:04:11 PM [vite] Internal server error: Failed to resolve import "./Cart" from "src/App.tsx". Does the file exist?'),
    "tsc watch": ("""
        [3:04:11 PM] File change detected. Starting incremental compilation...

        src/cart.ts:2:15 - error TS2339: Property 'lineItems' does not exist on type 'Cart'.

        2   return cart.lineItems.reduce((s, i) => s + i.price, 0);
                        ~~~~~~~~~

        [3:04:12 PM] Found 1 error. Watching for file changes.
        """, "src/cart.ts:2:15 - error TS2339: Property 'lineItems' does not exist on type 'Cart'."),
    "rust": ("""
           Compiling shop v0.1.0 (/Users/me/shop)
        error[E0308]: mismatched types
         --> src/main.rs:4:20
          |
        4 |     let total: u32 = "12";
          |                ---   ^^^^ expected `u32`, found `&str`
        """, "error[E0308]: mismatched types"),
    "go panic": ("""
        panic: runtime error: index out of range [3] with length 3

        goroutine 1 [running]:
        main.main()
        \t/Users/me/shop/main.go:9 +0x1d
        exit status 2
        """, "panic: runtime error: index out of range [3] with length 3"),
    "rails": ("""
        Started GET "/cart" for 127.0.0.1 at 2026-11-10 15:00:00
        NoMethodError (undefined method `total' for nil):
          app/controllers/carts_controller.rb:5:in `show'
        """, "NoMethodError (undefined method `total' for nil):"),
    "docker compose": ("""
        web-1  | Server starting
        web-1  | Error: connect ECONNREFUSED 172.18.0.2:5432
        web-1 exited with code 1
        """, "web-1  | Error: connect ECONNREFUSED 172.18.0.2:5432"),
    "npm": ("""
        > shop@1.0.0 build
        npm error code ELIFECYCLE
        npm error errno 1
        """, "npm error code ELIFECYCLE"),
    "jest": ("""
         FAIL  src/cart.test.js
          ● cart › totals items

            expect(received).toBe(expected) // Object.is equality
        """, "FAIL  src/cart.test.js"),
    "vitest": ("""
         × src/cart.test.ts > cart > totals 3ms
        AssertionError: expected NaN to be 37
        """, "AssertionError: expected NaN to be 37"),
    "access log 500": ("""
        15:15:20 GET / 200 3ms
        15:15:23 GET /cart 500 12.3 ms
        """, "15:15:23 GET /cart 500 12.3 ms"),
    "nodemon": ("""
        [nodemon] starting `node server.js`
        [nodemon] app crashed - waiting for file changes before starting...
        """, "[nodemon] app crashed - waiting for file changes before starting..."),
    "port in use": ("""
        Error: listen EADDRINUSE: address already in use :::3000
        """, "Error: listen EADDRINUSE: address already in use :::3000"),
    "zsh": ("zsh: command not found: pnpmm", "zsh: command not found: pnpmm"),
    "python logging": ("ERROR:root:payment failed after 3 retries", "ERROR:root:payment failed after 3 retries"),
    "django": ("Internal Server Error: /cart/", "Internal Server Error: /cart/"),
    "swift": ("/Users/me/App/ContentView.swift:12:5: error: cannot find 'foo' in scope",
              "/Users/me/App/ContentView.swift:12:5: error: cannot find 'foo' in scope"),
    "java": ('Exception in thread "main" java.lang.NullPointerException',
             'Exception in thread "main" java.lang.NullPointerException'),
    "eslint": ("✖ 2 problems (2 errors, 0 warnings)", "✖ 2 problems (2 errors, 0 warnings)"),
    "go test": ("--- FAIL: TestTotal (0.00s)", "--- FAIL: TestTotal (0.00s)"),
    "php": ("PHP Fatal error:  Uncaught Error: Call to undefined function foo()",
            "PHP Fatal error:  Uncaught Error: Call to undefined function foo()"),
    "log level": ('{"level":"error","msg":"db timeout"}', '{"level":"error","msg":"db timeout"}'),
    "mocha": ("  2 passing (8ms)\n  1 failing", "1 failing"),
}

FALSE_POSITIVES = [
    "[3:05:00 PM] Found 0 errors. Watching for file changes.",
    " ✓ Compiled /cart in 312ms",
    "Tests: 12 passed, 12 total",
    "10 passed, 0 failed",
    "Test Suites: 3 passed, 3 total",
    "src/app/error.tsx compiled",
    "registered onError handler",
    "abc1234 fix error handling in cart",
    "def5678 fix failed test for discount",
    "GET /cart 200 in 12ms",
    "no errors found",
    "starting with --log-level=error",
    "errorCount: 0",
    "INFO cache warmed (0 failures)",
    "error_handler.py loaded",
    "Debugger listening on ws://127.0.0.1:9229/abc",
    "warning: unused variable `x`",
    "  ➜  Local:   http://localhost:5173/",
]


class ErrorDetection(unittest.TestCase):
    def test_true_positives(self):
        for name, (text, want) in TRUE_POSITIVES.items():
            with self.subTest(name):
                self.assertEqual(headline(text), want)

    def test_false_positives(self):
        for line in FALSE_POSITIVES:
            with self.subTest(line):
                self.assertFalse(peek.is_error_line(line), line)

    def test_exception_names_containing_onerror_are_kept(self):
        # regression: "AssertionError" / "ConnectionError" contain "onError"
        self.assertTrue(peek.is_error_line("AssertionError: 100 != 95"))
        self.assertTrue(peek.is_error_line("requests.exceptions.ConnectionError: refused"))

    def test_traceback_is_one_cluster(self):
        lines = L(TRUE_POSITIVES["python unittest"][0])
        cl = peek.clusters(peek.find_errors(lines))
        joined = "\n".join(lines[cl[0][0]:cl[0][1]])
        self.assertIn("Traceback", joined)
        self.assertIn("AssertionError: 100 != 95", joined)

    def test_stale_error_detected(self):
        lines = L("""
            TypeError: x is undefined
                at foo (a.js:1:1)
            Restarting 'server.js'
            shop listening on http://localhost:3457
            """)
        blocks = peek.find_errors(lines)
        self.assertTrue(peek.healthy_after(lines, blocks[-1][1]))

    def test_not_stale_when_error_is_last(self):
        lines = L("""
            ready in 200ms
            TypeError: x is undefined
            """)
        blocks = peek.find_errors(lines)
        self.assertIsNone(peek.healthy_after(lines, blocks[-1][1]))


# ------------------------------------------------------------------------ cleaning

class Cleaning(unittest.TestCase):
    def test_ansi_and_crlf(self):
        raw = "\x1b[32mready\x1b[0m in 20ms\r\n\x1b[1;31mError:\x1b[0m boom\r\n"
        self.assertEqual(peek.to_lines(raw, raw_pty=True), ["ready in 20ms", "Error: boom"])

    def test_progress_bar_carriage_returns(self):
        raw = "downloading 10%\rdownloading 55%\rdownloading 100%\ndone\n"
        self.assertEqual(peek.to_lines(raw, raw_pty=True), ["downloading 100%", "done"])

    def test_backspace(self):
        self.assertEqual(peek.to_lines("abx\bc", raw_pty=True), ["abc"])

    def test_blank_runs_and_trailing_blanks(self):
        self.assertEqual(peek.to_lines("a\n\n\n\nb\n\n\n"), ["a", "", "b"])

    def test_compact_repeats_and_long_lines(self):
        out = peek.compact(["x", "x", "x", "y" * 500], width=100)
        self.assertEqual(out[0], "x   [repeated 3x]")
        self.assertTrue(out[1].endswith("(+400 chars)"))


class Redaction(unittest.TestCase):
    def test_tokens(self):
        cases = ["sk-ant-api03-abcdefghijklmnopqrstuvwxyz012345",
                 "ghp_abcdefghijklmnopqrstuvwxyz0123456789",
                 "AKIAABCDEFGHIJKLMNOP",
                 "sk_live_abcdefghijklmnop1234",
                 "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTYifQ.abcdefghijklmnop"]
        for c in cases:
            with self.subTest(c):
                r = peek.redact(f"token is {c} ok")
                self.assertNotIn(c, r)
                self.assertIn("[redacted]", r)

    def test_key_values_and_urls(self):
        r = peek.redact("DATABASE_URL=postgres://app:s3cretpw@db:5432/shop")
        self.assertNotIn("s3cretpw", r)
        r = peek.redact("export OPENAI_API_KEY=abc123def456ghi789")
        self.assertNotIn("abc123def456ghi789", r)
        r = peek.redact("Authorization: Bearer abcdefghijklmnop123456")
        self.assertNotIn("abcdefghijklmnop123456", r)
        r = peek.redact("password: hunter2xyz9")
        self.assertNotIn("hunter2xyz9", r)

    def test_leaves_normal_text_alone(self):
        for s in ["Tokens: 12,345 used", "auth: enabled", "GET /api/token 200",
                  "secret santa is fun", "TypeError: Cannot read properties of undefined"]:
            with self.subTest(s):
                self.assertEqual(peek.redact(s), s)

    def test_private_key_block(self):
        r = peek.redact("-----BEGIN OPENSSH PRIVATE KEY-----\nabc\ndef\n-----END OPENSSH PRIVATE KEY-----")
        self.assertNotIn("abc", r)


# --------------------------------------------------------------------- shells etc.

class LastCommand(unittest.TestCase):
    def test_zsh_default_prompt(self):
        lines = L("""
            ross@mac shop % ls
            a b
            ross@mac shop % npm run build
            Error: Cannot find module 'left-pad'
            ross@mac shop %
            """)
        self.assertEqual(peek.last_command(lines), (2, "npm run build"))

    def test_starship_two_line_prompt(self):
        lines = L("""
            ~/shop on main
            ❯ pytest -q
            1 failed, 2 passed
            ~/shop on main
            ❯
            """)
        self.assertEqual(peek.last_command(lines), (1, "pytest -q"))

    def test_bash_prompt(self):
        lines = ["me@box:~/shop$ make", "make: *** [all] Error 2", "me@box:~/shop$"]
        self.assertEqual(peek.last_command(lines), (0, "make"))

    def test_busy_terminal_has_no_prompt(self):
        self.assertIsNone(peek.last_command(["listening on :3000", "GET / 200"]))


class NewOutput(unittest.TestCase):
    def test_append_only(self):
        a = ["one", "two", "three"]
        st = peek.anchor_of(a)
        self.assertEqual(peek.find_new_start(a + ["four", "five"], st), 3)

    def test_nothing_new(self):
        a = ["one", "two", "three"]
        self.assertEqual(peek.find_new_start(a, peek.anchor_of(a)), 3)

    def test_screen_cleared(self):
        st = peek.anchor_of(["crash", "Failed running 'server.js'", "waiting"])
        self.assertIsNone(peek.find_new_start(["Restarting", "listening"], st))

    def test_repeated_block_prefers_old_position(self):
        block = ["Restarting 'server.js'", "listening on 3000", "ready"]
        st = peek.anchor_of(["boot"] + block)
        later = ["boot"] + block + ["GET /"] + block
        self.assertEqual(peek.find_new_start(later, st), 4)

    def test_scrollback_trimmed_from_top(self):
        a = [f"line {i}" for i in range(100)]
        st = peek.anchor_of(a)
        b = a[30:] + ["new 1", "new 2"]
        self.assertEqual(b[peek.find_new_start(b, st):], ["new 1", "new 2"])


class Commands(unittest.TestCase):
    def test_pretty_command(self):
        self.assertEqual(peek.pretty_command("node /opt/homebrew/bin/npm run dev"), "npm run dev")
        self.assertEqual(peek.pretty_command("/usr/bin/python3 -m pytest -q"), "python3 -m pytest -q")
        self.assertEqual(peek.pretty_command("-zsh"), "zsh")
        self.assertEqual(peek.pretty_command("node /Users/me/shop/node_modules/.bin/next dev"), "next dev")

    def test_foreground_process(self):
        plist = [
            {"pid": 10, "ppid": 1, "pgid": 10, "tpgid": 20, "tty": "ttys001", "cmd": "login -pf me"},
            {"pid": 11, "ppid": 10, "pgid": 11, "tpgid": 20, "tty": "ttys001", "cmd": "-zsh"},
            {"pid": 20, "ppid": 11, "pgid": 20, "tpgid": 20, "tty": "ttys001", "cmd": "node /x/bin/npm run dev"},
            {"pid": 21, "ppid": 20, "pgid": 20, "tpgid": 20, "tty": "ttys001", "cmd": "node next dev"},
        ]
        self.assertEqual(peek.foreground(plist)["pid"], 20)

    def test_short_path(self):
        home = peek.HOME
        self.assertEqual(peek.short_path(home + "/src/shop"), "~/src/shop")
        self.assertEqual(peek.short_path("/private/tmp/" + "x" * 60 + "/scratchpad/shop"), "…/scratchpad/shop")


def make_tab(n, command, cwd="/Users/me/shop", ports=(), state="busy", text="ok", app="Terminal", tty=None):
    t = peek.Tab(app, tty=tty or f"ttys00{n}", cwd=cwd, text=text, command=command)
    t.n, t.ports, t.state = n, list(ports), state
    return t


class Resolve(unittest.TestCase):
    def setUp(self):
        self.tabs = [
            make_tab(1, "zsh", state="idle", text="me@mac shop % git status\nclean\nme@mac shop %"),
            make_tab(2, "npm run dev", ports=[3000], text="ready on 3000\nGET / 200"),
            make_tab(3, "python3 -m pytest -f", cwd="/Users/me/api", text="1 failed"),
            make_tab(4, "tail -f logs/app.log", text="INFO payment webhook ok"),
            make_tab(5, "claude", state="self", text="agent ui"),
        ]

    def r(self, q):
        t = peek.resolve(self.tabs, q)
        return t.n if t else None

    def test_number_id_port(self):
        self.assertEqual(self.r("3"), 3)
        self.assertEqual(self.r("ttys004"), 4)
        self.assertEqual(self.r("3000"), 2)
        self.assertEqual(self.r(":3000"), 2)

    def test_words_and_synonyms(self):
        self.assertEqual(self.r("pytest"), 3)
        self.assertEqual(self.r("api"), 3)
        self.assertEqual(self.r("server"), 2)
        self.assertEqual(self.r("tests"), 3)
        self.assertEqual(self.r("app.log"), 4)

    def test_content_fallback(self):
        self.assertEqual(self.r("webhook"), 4)

    def test_never_picks_self_by_text(self):
        self.assertEqual(self.r("agent ui"), None)

    def test_no_match(self):
        self.assertIsNone(self.r("kubernetes"))


# --------------------------------------------------------------------- CLI pieces

class Cli(unittest.TestCase):
    def run_main(self, argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = peek.main(argv)
        return rc, buf.getvalue()

    def test_version_and_help(self):
        rc, o = self.run_main(["--version"])
        self.assertEqual((rc, o.strip()), (0, f"peek {peek.__version__}"))
        rc, o = self.run_main(["help"])
        self.assertIn("peek errors", o)

    def test_skill_file_matches_embedded_copy(self):
        with open(os.path.join(ROOT, "skill", "SKILL.md")) as f:
            self.assertEqual(f.read(), peek.SKILL_MD)
        rc, o = self.run_main(["skill"])
        self.assertEqual(o, peek.SKILL_MD)

    def test_skill_install_to_dir(self):
        d = tempfile.mkdtemp()
        try:
            rc, _ = self.run_main(["skill", "--install", "--dir", d])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(os.path.join(d, "peek", "SKILL.md")))
            self.run_main(["skill", "--uninstall", "--dir", d])
            self.assertFalse(os.path.exists(os.path.join(d, "peek")))
        finally:
            shutil.rmtree(d, ignore_errors=True)


class Verdicts(unittest.TestCase):
    def test_clean_restart_is_not_called_fixed(self):
        t = make_tab(2, "node --watch server.js", ports=[3457])
        v = peek.clean_verdict(t, ["Restarting 'server.js'", "shop listening on http://localhost:3457"])
        self.assertIn("nothing has run the fixed code yet", v)
        self.assertIn("curl localhost:3457", v)

    def test_request_after_restart_counts(self):
        t = make_tab(2, "node --watch server.js", ports=[3457])
        v = peek.clean_verdict(t, ["Restarting 'server.js'", "listening", "15:16:02 GET /cart"])
        self.assertEqual(v, "✓ no errors in this output")

    def test_in_project(self):
        t = make_tab(1, "npm run dev", cwd="/Users/me/shop")
        self.assertTrue(peek.in_project(t, "/Users/me/shop"))
        self.assertTrue(peek.in_project(t, "/Users/me/shop/src"))
        self.assertFalse(peek.in_project(t, "/Users/me/other"))


class Round3(unittest.TestCase):
    """Fixes from the second fresh-agent test."""

    def test_cleared_screen_starts_at_latest_restart(self):
        # Terminal.app after `node --watch` clears: leftovers of the old crash + the new restart
        lines = ["Change detected in '/a/server.js'", "Restarting 'server.js'",
                 "node:internal/modules/cjs/loader:1607", "  throw err;",
                 "Change detected in '/a/server.js'", "Restarting 'server.js'",
                 "shop listening on http://localhost:3457"]
        self.assertEqual(peek.cleared_start(lines), 4)
        self.assertEqual(peek.cleared_start(["no", "markers"]), 0)

    def test_tidy_block_relative_paths_and_folded_frames(self):
        block = ["Error: Cannot find module './carts'", "Require stack:", "- /Users/me/shop/server.js",
                 "    at Module._resolveFilename (node:internal/modules/cjs/loader:1603:15)",
                 "    at Module._load (node:internal/modules/cjs/loader:1370:5)",
                 "    at Object.<anonymous> (/Users/me/shop/server.js:2:23)",
                 "    at Server.emit (node:events:514:20)"]
        out = peek.tidy_block(block, "/Users/me/shop")
        self.assertIn("- ./server.js", out)
        self.assertIn("    … 2 library frames", out)
        self.assertIn("    at Object.<anonymous> (./server.js:2:23)", out)
        self.assertIn("    at Server.emit (node:events:514:20)", out)  # a single frame stays

    def test_crashed_server_outranks_log_tail(self):
        server = make_tab(2, "node --watch server.js")
        self.assertTrue(peek.crashed(server, ["Error: x", "Failed running 'server.js'. Waiting for file changes before restarting..."]))
        logs = make_tab(4, "tail -f app.log")
        self.assertFalse(peek.crashed(logs, ["12:01:07 ERROR payment webhook failed"]))
        self.assertIn("tail", peek.LOG_VIEWERS)

    def test_down_port_label(self):
        t = make_tab(2, "node server.js")
        t.down_ports = [3457]
        self.assertEqual(t.port_label(), ":3457 down")
        t.ports = [3457]
        self.assertEqual(t.port_label(), ":3457")


@unittest.skipUnless(os.environ.get("PEEK_INTEGRATION") and shutil.which("tmux"), "set PEEK_INTEGRATION=1")
class TmuxIntegration(unittest.TestCase):
    """End to end against a real tmux pane: list, errors, show, --wait."""

    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.env = dict(os.environ, PEEK_HOME=self.home)
        self.sess = f"peekci{os.getpid()}"
        script = ("import time,sys; print('server ready on 4321'); sys.stdout.flush(); time.sleep(1.5); "
                  "print('TypeError: Cannot read properties of undefined'); print('    at cart (cart.js:2:5)'); "
                  "sys.stdout.flush(); time.sleep(60)")
        subprocess.run(["tmux", "new-session", "-d", "-s", self.sess, "-x", "120", "-y", "30",
                        sys.executable, "-c", script], check=True)

    def tearDown(self):
        subprocess.run(["tmux", "kill-session", "-t", self.sess], capture_output=True)
        shutil.rmtree(self.home, ignore_errors=True)

    def peek(self, *a):
        p = subprocess.run([sys.executable, os.path.join(ROOT, "peek.py"), *a], env=self.env,
                           capture_output=True, text=True, timeout=60)
        return p.returncode, p.stdout

    def test_end_to_end(self):
        import time
        time.sleep(0.6)
        rc, o = self.peek("--json")
        panes = [t for t in json.loads(o)["terminals"] if t["app"] == "tmux" and "python" in (t["command"] or "")]
        self.assertTrue(panes, o)
        n = str(panes[0]["n"])
        rc, o = self.peek(n)  # first look: only the "ready" line
        self.assertIn("server ready", o)
        rc, o = self.peek(n, "--wait", "TypeError", "--timeout", "10")
        self.assertEqual(rc, 0, o)
        self.assertIn("TypeError: Cannot read properties of undefined", o)
        body = o.split("\n", 1)[1]  # the header repeats the command line
        self.assertNotIn("server ready", body)  # only what's new
        rc, o = self.peek("errors", n, "--json")
        self.assertEqual(json.loads(o)["terminals"][0]["headline"], "TypeError: Cannot read properties of undefined")


class Run(unittest.TestCase):
    """`peek run` captures output and the exit code, in a subprocess (non-tty: tee mode)."""

    def test_run_captures_output_and_exit_code(self):
        home = tempfile.mkdtemp()
        try:
            env = dict(os.environ, PEEK_HOME=home)
            code = "import sys; print('Error: boom'); sys.exit(3)"
            p = subprocess.run([sys.executable, os.path.join(ROOT, "peek.py"), "run", "--",
                                sys.executable, "-c", code], env=env, capture_output=True, text=True,
                               stdin=subprocess.DEVNULL, timeout=30)
            self.assertEqual(p.returncode, 3)
            self.assertIn("Error: boom", p.stdout)
            metas = [f for f in os.listdir(os.path.join(home, "runs")) if f.endswith(".json")]
            self.assertEqual(len(metas), 1)
            with open(os.path.join(home, "runs", metas[0])) as f:
                m = json.load(f)
            self.assertEqual((m["status"], m["code"]), ("exited", 3))
            p2 = subprocess.run([sys.executable, os.path.join(ROOT, "peek.py"), "errors", "--json"],
                                env=env, capture_output=True, text=True, timeout=30)
            data = json.loads(p2.stdout)
            runs = [t for t in data["terminals"] if t["terminal"]["app"] == "peek run"]
            self.assertEqual(len(runs), 1)
            self.assertEqual(runs[0]["headline"], "Error: boom")
        finally:
            shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
