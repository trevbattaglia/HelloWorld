# Sleeper fantasy NBA agent

**Task:** let Claude see my Sleeper fantasy NBA team and make moves for me (set lineups, add/drop) by driving a real Chrome window.

**How it works:**
- `sleeper.py`: read-only CLI for Sleeper's public API (no login needed). Python 3 standard library only, so no `requirements.txt`.
- `.mcp.json`: gives Claude Code the [Playwright MCP](https://github.com/microsoft/playwright-mcp) browser tools. Chrome uses a persistent profile in `.browser-profile/` (gitignored), so you log in once and stay logged in.
- `CLAUDE.md`: rules Claude follows here. Mainly: confirm every move before submitting, never handle your password, never trade unless asked.

Sleeper's public API is read-only, so moves go through the website UI like a person would. This is automation of your own account and may be against Sleeper's terms; use it at your own risk.

## Setup (on your own computer)

Needs: Google Chrome, Node.js 18+, Python 3, and [Claude Code](https://code.claude.com).

```bash
cd 2026-10-20-sleeper-nba-agent
export SLEEPER_USERNAME=your_sleeper_username
export SLEEPER_LEAGUE_ID=123...   # only if you're in more than one NBA league
python sleeper.py leagues         # sanity check
claude                            # approve the "playwright" MCP server when prompted
```

First run: ask Claude to "open sleeper.com". A Chrome window opens; log in yourself (Sleeper's email/SMS code). The session is saved in `.browser-profile/`.

## Using it

Examples to say to Claude:
- "Set my lineup for tonight": it checks who plays and who's hurt, proposes a lineup, and makes the swaps after you OK it.
- "Who's the best C on waivers? Should I drop anyone for him?"
- "How's my matchup looking this week?"

Direct CLI use:

```bash
python sleeper.py roster
python sleeper.py matchup [--week N]
python sleeper.py free-agents --pos C --limit 20
python sleeper.py trending
```

## Status / outputs

- No output files; everything happens in Sleeper.
- `sleeper.py` was tested against mocked API responses only. Sleeper wasn't reachable from the sandbox it was built in, so the first real run may need small fixes.
- The browser side has no hardcoded selectors: Claude reads the page and clicks like a person, so it should survive Sleeper UI changes.
