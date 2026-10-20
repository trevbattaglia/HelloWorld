#!/usr/bin/env python3
"""Read-only helper for the public Sleeper API (fantasy NBA).

Usage:
  python sleeper.py leagues
  python sleeper.py roster
  python sleeper.py matchup [--week N]
  python sleeper.py free-agents [--pos PG] [--limit 30]
  python sleeper.py trending [--limit 25]

Set SLEEPER_USERNAME (and SLEEPER_LEAGUE_ID if you're in more than one NBA
league), or pass --user / --league. Standard library only.
"""

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

API = "https://api.sleeper.app/v1"
CACHE = Path(__file__).parent / ".cache" / "players_nba.json"
CACHE_MAX_AGE = 24 * 3600


def get(path):
    with urllib.request.urlopen(f"{API}{path}", timeout=30) as resp:
        return json.load(resp)


def players():
    # The full player list is ~5MB; Sleeper asks callers to fetch it at most once a day.
    if CACHE.exists() and time.time() - CACHE.stat().st_mtime < CACHE_MAX_AGE:
        return json.loads(CACHE.read_text())
    data = get("/players/nba")
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(data))
    return data


def describe(pid, db):
    p = db.get(pid) or {}
    name = p.get("full_name") or f"{p.get('first_name', '')} {p.get('last_name', '')}".strip() or pid
    pos = "/".join(p.get("fantasy_positions") or []) or "?"
    team = p.get("team") or "FA"
    injury = f" [{p['injury_status']}]" if p.get("injury_status") else ""
    return f"{name} ({pos}, {team}){injury}  id={pid}"


def find_user(username):
    user = get(f"/user/{username}")
    if not user:
        sys.exit(f"No Sleeper user named {username!r}")
    return user


def find_league(user, league_id, season):
    leagues = get(f"/user/{user['user_id']}/leagues/nba/{season}") or []
    if league_id:
        match = [lg for lg in leagues if lg["league_id"] == league_id]
        if not match:
            sys.exit(f"League {league_id} not found for {user['display_name']} in {season}")
        return match[0]
    if len(leagues) != 1:
        names = "\n".join(f"  {lg['league_id']}  {lg['name']}" for lg in leagues) or "  (none)"
        sys.exit(f"Set SLEEPER_LEAGUE_ID / --league; NBA leagues for {season}:\n{names}")
    return leagues[0]


def my_roster(league, user):
    for r in get(f"/league/{league['league_id']}/rosters"):
        if r.get("owner_id") == user["user_id"] or user["user_id"] in (r.get("co_owners") or []):
            return r
    sys.exit("You don't own a roster in this league")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["leagues", "roster", "matchup", "free-agents", "trending"])
    ap.add_argument("--user", default=os.environ.get("SLEEPER_USERNAME"))
    ap.add_argument("--league", default=os.environ.get("SLEEPER_LEAGUE_ID"))
    ap.add_argument("--week", type=int)
    ap.add_argument("--pos", help="filter free agents by position, e.g. PG, C")
    ap.add_argument("--limit", type=int, default=30)
    args = ap.parse_args()

    state = get("/state/nba")
    season = state["season"]

    if args.command == "trending":
        db = players()
        for t in get(f"/players/nba/trending/add?lookback_hours=24&limit={args.limit}"):
            print(f"+{t['count']:>5}  {describe(t['player_id'], db)}")
        return

    if not args.user:
        sys.exit("Set SLEEPER_USERNAME or pass --user")
    user = find_user(args.user)

    if args.command == "leagues":
        for lg in get(f"/user/{user['user_id']}/leagues/nba/{season}") or []:
            print(f"{lg['league_id']}  {lg['name']}  ({lg['status']})")
        return

    league = find_league(user, args.league, season)
    db = players()

    if args.command == "roster":
        r = my_roster(league, user)
        s = r.get("settings", {})
        print(f"{league['name']} - record {s.get('wins', 0)}-{s.get('losses', 0)}-{s.get('ties', 0)}")
        print(f"Lineup slots: {', '.join(league.get('roster_positions') or [])}\n")
        starters = r.get("starters") or []
        reserve = r.get("reserve") or []
        slots = league.get("roster_positions") or []
        print("STARTERS")
        for i, pid in enumerate(starters):
            slot = slots[i] if i < len(slots) else "?"
            print(f"  {slot:<6} {describe(pid, db) if pid != '0' else '(empty)'}")
        print("BENCH")
        for pid in r.get("players") or []:
            if pid not in starters and pid not in reserve:
                print(f"         {describe(pid, db)}")
        if reserve:
            print("IR")
            for pid in reserve:
                print(f"         {describe(pid, db)}")

    elif args.command == "matchup":
        week = args.week or state.get("week") or 1
        r = my_roster(league, user)
        matchups = get(f"/league/{league['league_id']}/matchups/{week}") or []
        mine = next((m for m in matchups if m["roster_id"] == r["roster_id"]), None)
        if not mine:
            sys.exit(f"No matchup found for week {week}")
        opp = next((m for m in matchups if m.get("matchup_id") == mine.get("matchup_id")
                    and m["roster_id"] != mine["roster_id"]), None)
        owners = {u["user_id"]: u for u in get(f"/league/{league['league_id']}/users")}
        rosters = {x["roster_id"]: x for x in get(f"/league/{league['league_id']}/rosters")}
        for label, m in (("YOU", mine), ("OPPONENT", opp)):
            if not m:
                continue
            owner = owners.get(rosters[m["roster_id"]].get("owner_id"), {})
            team = (owner.get("metadata") or {}).get("team_name") or owner.get("display_name", "?")
            print(f"{label}: {team} - {m.get('points', 0):.1f} pts (week {week})")
            pts = m.get("players_points") or {}
            for pid in m.get("starters") or []:
                if pid != "0":
                    print(f"  {pts.get(pid, 0):>6.1f}  {describe(pid, db)}")
            print()

    elif args.command == "free-agents":
        rostered = set()
        for r in get(f"/league/{league['league_id']}/rosters"):
            rostered.update(r.get("players") or [])
        pool = [
            (pid, p) for pid, p in db.items()
            if pid not in rostered and p.get("active") and p.get("team")
            and (not args.pos or args.pos.upper() in (p.get("fantasy_positions") or []))
        ]
        # search_rank is Sleeper's own popularity/value ordering; lower is better.
        pool.sort(key=lambda x: x[1].get("search_rank") or 10**9)
        for pid, _ in pool[: args.limit]:
            print(describe(pid, db))


if __name__ == "__main__":
    main()
