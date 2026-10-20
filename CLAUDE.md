# Scratch space

General-purpose sandbox for one-off tasks, unrelated to other projects. Keep everything lightweight.

## Rules

- Every task gets its own folder at the root named `YYYY-MM-DD-short-description` (e.g. `2026-10-20-csv-cleanup`).
- Each folder has a short `README.md`: what the task was, how to run anything in it, and any outputs.
- Keep tasks self-contained: no shared code between folders unless asked.
- Python: per-folder `requirements.txt`. Node: per-folder `package.json`.
- Never commit secrets, API keys, or `.env` files.
- When adding a task folder, add a one-line entry for it to the index in the root `README.md`.
- Commit directly to the default branch (`master`) with clear messages; no PRs needed.
- Prefer simple, minimal solutions over frameworks.
