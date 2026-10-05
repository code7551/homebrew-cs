#!/usr/bin/python3
"""Captures the real cs screens for the launch film, fed with made-up chats.

Runs the actual claude-sessions code against a throwaway world (fake home
folders, fake chats, fake projects), records every screen it draws, and turns
the terminal output into a grid of coloured cells in frames.json, which
film.html draws. Nothing here reads or writes your real chats.

    /usr/bin/python3 promo/capture.py
"""
import contextlib, io, json, os, re, shutil, sys, tempfile, time
from importlib.machinery import SourceFileLoader

HERE = os.path.dirname(os.path.abspath(__file__))
COLS, ROWS = 100, 32
SHOWN_HOME = "/Users/you"  # what the film shows instead of the throwaway folders
os.environ.update(COLUMNS=str(COLS), LINES=str(ROWS))
REAL_HOME = os.path.expanduser("~")  # checked against at the end: must not appear in the film


class FakeTTY(io.StringIO):
    def isatty(self):
        return True


# Load cs as if it were talking to a colour terminal, so it emits its real colours.
real_stdout, sys.stdout = sys.stdout, FakeTTY()
cs = SourceFileLoader("cs", os.path.join(HERE, "..", "claude-sessions")).load_module()
sys.stdout = real_stdout

WORLD = tempfile.mkdtemp(prefix="cs-film-")
HOME_A, HOME_B = os.path.join(WORLD, "mac-a"), os.path.join(WORLD, "mac-b")
NOW = time.time()


# ---- the made-up world ---------------------------------------------------
CHATS_A = [  # (project, title, age in minutes)
    ("kiosk-ui", "make the kiosk checkout work offline", 12),
    ("orbit-api", "rate limiter returns 500 under load", 41),
    ("lumen-app", "dark mode for the settings screen", 130),
    ("kiosk-ui", "kiosk receipt printer keeps timing out", 300),
    ("ledger", "monthly totals are off by one cent", 1500),
    ("atlas-docs", "rewrite the getting-started guide", 1700),
    ("pixel-forge", "speed up the sprite exporter", 2900),
    ("tidepool", "move the cron jobs onto a queue", 4400),
    ("nightjar", "push notifications on Android 16", 5800),
    ("kiosk-ui", "add QR payments to the kiosk", 7300),
    ("harbor-infra", "terraform plan shows drift on the VPC", 8700),
    ("sundial", "timezone bug in the booking calendar", 11600),
    ("orbit-api", "add pagination to /v2/orders", 13000),
    ("lumen-app", "fix the flicker when the list refreshes", 15900),
]
CHATS_B = [
    ("sundial", "recurring events skip daylight saving", 25),
    ("nightjar", "crash on cold start after update", 2600),
    ("atlas-docs", "add a search box to the docs site", 9000),
]
# Folders in ~/GitHub, newest first by Finder's "Date Added" (minutes ago).
FOLDERS = [("comet-cli", 38), ("kiosk-ui", 1500), ("orbit-api", 5000), ("lumen-app", 9000),
           ("ledger", 13000), ("atlas-docs", 20000), ("pixel-forge", 26000),
           ("tidepool", 33000), ("nightjar", 41000), ("harbor-infra", 50000), ("sundial", 64000)]


def fake_id(n):
    return f"{n:08x}-4c7e-4a1b-9d2e-{n * 7919:012x}"


def make_mac(home, chats, start):
    claude = os.path.join(home, ".claude")
    for d in ("Downloads", "GitHub"):
        os.makedirs(os.path.join(home, d), exist_ok=True)
    for name, _ in FOLDERS:
        os.makedirs(os.path.join(home, "GitHub", name), exist_ok=True)
    for i, (proj, title, age) in enumerate(chats):
        cwd = os.path.join(home, "GitHub", proj)
        pdir = os.path.join(claude, "projects", re.sub(r"[^a-zA-Z0-9]", "-", cwd))
        os.makedirs(pdir, exist_ok=True)
        path = os.path.join(pdir, fake_id(start + i) + ".jsonl")
        with open(path, "w") as f:
            f.write(json.dumps({"type": "user", "cwd": cwd, "sessionId": fake_id(start + i),
                                "message": {"content": title}}) + "\n")
        os.utime(path, (NOW - age * 60, NOW - age * 60))
    return claude


def use_mac(home, claude):
    """Point cs at one of the fake Macs."""
    os.environ["HOME"] = home
    cs.CLAUDE, cs.DOWNLOADS = claude, os.path.join(home, "Downloads")
    cs.CACHE = os.path.join(home, "cache.json")


def unhome(text):
    for home in (HOME_A, HOME_B):
        text = text.replace(home, SHOWN_HOME)
    return text


# ---- capture every screen cs draws -------------------------------------------
screens = []
_show_page = cs.show_page


def recording_show_page(**kw):
    kw["details"] = [(label, unhome(value)) for label, value in kw["details"]]
    buf = FakeTTY()
    with contextlib.redirect_stdout(buf):
        _show_page(**kw)
    screens.append(buf.getvalue())


class NoLoading:  # the loading screen runs in a thread; the film doesn't need it
    def __init__(self, *a, **k): pass
    def __enter__(self): return self
    def __exit__(self, *a): pass


cs.show_page = recording_show_page
cs.Loading = NoLoading
cs.subprocess = type("NoSubprocess", (), {"run": staticmethod(lambda *a, **k: None)})  # no Finder
cs.added_time = lambda path: NOW - dict(FOLDERS).get(os.path.basename(path), 99999) * 60


def run(rows, recent, actions, incoming=()):
    """Drive the real picker with key presses; return (screens drawn, result)."""
    screens.clear()
    keys = iter(actions)

    def next_action():
        try:
            return next(keys)
        except StopIteration:
            raise EOFError
    result = cs.pick(rows, recent, ROWS - cs.PANEL_LINES, "", "sessions", next_action,
                     lambda: False, incoming=incoming)
    return list(screens), result


def recent_of(rows):
    by = {}
    for r in rows:
        p = by.setdefault(r["cwd"], {"cwd": r["cwd"], "mtime": r["mtime"], "count": 0})
        p["count"] += 1
    return list(by.values())


def banner(row, new=False, size=None):
    row = dict(row, cwd=unhome(row["cwd"]))
    if size:
        row["size"] = size
    return cs.launch_banner(row, new)


# ---- a tiny terminal: ANSI text -> grid of cells ---------------------------------
def to_grid(text, rows=ROWS, cols=COLS):
    grid = [[(" ", None, None, 0, 0) for _ in range(cols)] for _ in range(rows)]
    r = c = 0
    fg = bg = None
    bold = ul = 0
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\033":
            m = re.match(r"\033\[([0-9;?]*)([A-Za-z])", text[i:])
            params, cmd = m.group(1), m.group(2)
            i += len(m.group(0))
            if cmd == "H":
                r = c = 0
            elif cmd == "K" and r < rows:
                for x in range(c, cols):
                    grid[r][x] = (" ", None, None, 0, 0)
            elif cmd == "J":
                for y in range(r, rows):
                    for x in range(c if y == r else 0, cols):
                        grid[y][x] = (" ", None, None, 0, 0)
            elif cmd == "m":
                p = [int(x) for x in params.split(";") if x != ""] or [0]
                k = 0
                while k < len(p):
                    if p[k] == 0:
                        fg = bg = None
                        bold = ul = 0
                    elif p[k] == 1:
                        bold = 1
                    elif p[k] == 4:
                        ul = 1
                    elif p[k] in (38, 48) and k + 2 < len(p) and p[k + 1] == 5:
                        if p[k] == 38:
                            fg = p[k + 2]
                        else:
                            bg = p[k + 2]
                        k += 2
                    k += 1
            continue
        if ch == "\n":
            r, c = r + 1, 0
        elif r < rows and c < cols:
            grid[r][c] = (ch, fg, bg, bold, ul)
            c += 1
        i += 1
    # rows of runs: [start column, text, fg, bg, bold, underline]; blank cells dropped
    out = []
    for row in grid:
        runs = []
        for x, (ch, f, b, bo, u) in enumerate(row):
            if ch == " " and b is None and not u:
                continue
            if runs and runs[-1][0] + len(runs[-1][1]) == x and runs[-1][2:] == [f, b, bo, u]:
                runs[-1][1] += ch
            else:
                runs.append([x, ch, f, b, bo, u])
        out.append(runs)
    return out


def banner_grid(text):
    lines = text.split("\n")
    return to_grid(text, rows=len(lines), cols=COLS)


# ---- the scenes -------------------------------------------------------------------
claude_a = make_mac(HOME_A, CHATS_A, 0x3a1f00)
claude_b = make_mac(HOME_B, CHATS_B, 0x7c2e00)
use_mac(HOME_A, claude_a)
os.chdir(os.path.join(HOME_A, "GitHub"))
rows_a = cs.load_sessions({"done": 0, "total": 0})
recent_a = recent_of(rows_a)

film = {"cols": COLS, "rows": ROWS, "scenes": {}, "banners": {}}

# 1. the list, then search "kiosk", ↓, Enter
shots, picked = run(list(rows_a), recent_a,
                    [("text", ch) for ch in "kiosk"] + ["down", "enter"])
film["scenes"]["search"] = [to_grid(s) for s in shots]
film["banners"]["resume"] = banner_grid(banner(picked[1], size=18_400_000))

# 2. Tab: new session, → into ~/GitHub, ↓ to the newest folder, Enter
shots, picked = run(list(rows_a), recent_a, ["tab", "next", "down", "down", "down", "enter"])
film["scenes"]["new"] = [to_grid(s) for s in shots]
film["banners"]["new"] = banner_grid(banner(picked[1], new=True))

# 3. → menu on the newest chat, ↓ Save for another Mac, Enter
shots, picked = run(list(rows_a), recent_a, ["down", "next", "down", "enter"])
film["scenes"]["save"] = [to_grid(s) for s in shots]
bundle = next(os.path.join(cs.DOWNLOADS, f) for f in os.listdir(cs.DOWNLOADS)
              if f.endswith(cs.BUNDLE_EXT))
film["bundle_name"] = os.path.basename(bundle)

# 4. the other Mac: the file is in Downloads, Enter imports and resumes
shutil.copy(bundle, os.path.join(HOME_B, "Downloads"))
use_mac(HOME_B, claude_b)
rows_b = cs.load_sessions({"done": 0, "total": 0})
shots, picked = run(list(rows_b), recent_of(rows_b), ["enter"], incoming=cs.incoming_bundles())
film["scenes"]["import"] = [to_grid(s) for s in shots]
film["banners"]["import"] = banner_grid(banner(picked[1], size=1_200_000))

out = os.path.join(HERE, "frames.json")
with open(out, "w") as f:
    json.dump(film, f, ensure_ascii=False, separators=(",", ":"))
shutil.rmtree(WORLD)

# Privacy: the film must only contain made-up data.
text = open(out).read()
for bad in (REAL_HOME, os.path.basename(REAL_HOME), WORLD):
    assert bad not in text, f"leaked: {bad}"
print(f"wrote {out}: " + ", ".join(f"{k} {len(v)} screens" for k, v in film["scenes"].items()))
