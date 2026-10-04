# cs

A searchable terminal picker for your [Claude Code](https://claude.com/claude-code) chats.
Run `cs`, find a chat, press Enter, and it opens in that chat's project folder.
Or browse to any folder and start a new chat there.

```
┌─[ SESSIONS ]─[ NEW SESSION ]──────────────────────────────────[ page 1/1 ]─┐
│                  ▓▒░  C L A U D E   S E S S I O N S  ░▒▓                   │
│  ❯ kiosk█                                                3 of 50 sessions  │
│    WHEN              PROJECT     SESSION                                   │
│    ────────────────  ──────────  ───────────────────────────────────────── │
│  ▶ Today 19:30       play-kiosk  Tablet kiosk check-in screen              │
│    Yesterday 18:40   play-kiosk  Backoffice booking report                 │
│    30 Sep 2026       play-kiosk  Kiosk payment flow                        │
├────────────────────────────────────────────────────────────────────────────┤
│  dir  /Users/you/GitHub/play-kiosk                                         │
│  id   8f14e45f-ceea-467a-9575-a8c0b2c1d3e4                                 │
└─[↑↓ select]─[⏎ resume]─[tab new session]─[esc clear]───────────────────────┘
```

## Install

```sh
brew install code7551/cs/cs
```

Then add this line to `~/.zshrc` and open a new terminal:

```sh
(( $+commands[claude-sessions] )) && eval "$(claude-sessions init zsh)"
```

Needs zsh and the `claude` CLI. It uses the Python 3 that comes with macOS (`/usr/bin/python3`).

## Use

**Resume a chat** (the SESSIONS tab):

| Key | Action |
|---|---|
| type | Search project names and chat titles |
| ↑ ↓ | Move the selection |
| Enter | Resume the selected chat in its project folder |
| ← → | Previous / next page |
| Backspace, Ctrl-U | Delete a character / clear the search |
| Esc | Clear the search, or quit if it is empty |

**Start a new chat** (pick `+ New session` at the top, or press Tab): a folder
browser opens on your current folder and the folders of your recent chats.

| Key | Action |
|---|---|
| Enter | Start a new session in the highlighted folder |
| → | Open the folder |
| ← | Go up to the parent folder |
| type | Filter folders (start with `.` to see hidden ones) |
| type a name, then Enter on `+ create folder` | Make a new folder and open it |
| Esc | Clear what you typed, or go back to SESSIONS |

```sh
cs            # all chats, newest first
cs kiosk      # start with "kiosk" already in the search box
cs --new      # go straight to the folder browser for a new session
cs -n 20      # 20 per page (default 25, fewer on short windows)
```

Session titles are cached in `~/.cache/claude-sessions.json`. After the
first run, it only reads lines added since last time, so the list opens
almost at once even with very large sessions.

## Update / remove

```sh
brew upgrade cs
brew uninstall cs   # then remove the eval line from ~/.zshrc
```
