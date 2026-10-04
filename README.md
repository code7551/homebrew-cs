# cs

A searchable terminal picker for your [Claude Code](https://claude.com/claude-code) chats.
Run `cs`, find a chat, press Enter, and it opens in that chat's project folder.

```
┌───────────────────────────────────────────────────────────────[ page 1/1 ]─┐
│                  ▓▒░  C L A U D E   S E S S I O N S  ░▒▓                   │
│  ❯ kiosk█                                                3 of 50 sessions  │
│    WHEN              PROJECT     SESSION                                   │
│    ────────────────  ──────────  ───────────────────────────────────────── │
│  ▶ Today 17:19       play-kiosk  Tablet kiosk check-in screen              │
│    Yesterday 16:29   play-kiosk  Backoffice booking report                 │
│    30 Sep 2026       play-kiosk  Kiosk payment flow                        │
├────────────────────────────────────────────────────────────────────────────┤
│  dir  /Users/you/GitHub/play-kiosk                                         │
│  id   8f14e45f-ceea-467a-9575-a8c0b2c1d3e4                                 │
└─[↑↓ select]─[⏎ resume]─[esc clear]─────────────────────────────────────────┘
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

| Key | Action |
|---|---|
| type | Search project names and chat titles |
| ↑ ↓ | Move the selection |
| Enter | Resume the selected chat in its project folder |
| ← → | Previous / next page |
| Backspace, Ctrl-U | Delete a character / clear the search |
| Esc | Clear the search, or quit if it is empty |

```sh
cs            # all chats, newest first
cs kiosk      # start with "kiosk" already in the search box
cs -n 20      # 20 chats per page (default 25, fewer on short windows)
```

Session titles are cached in `~/.cache/claude-sessions.json`. After the
first run, it only reads lines added since last time, so the list opens
almost at once even with very large sessions.

## Update / remove

```sh
brew upgrade cs
brew uninstall cs   # then remove the eval line from ~/.zshrc
```
