# Security

## Rules (non-negotiable)
1. **Never commit secrets, API keys, or live databases.**
2. Use `.env.template` only as a placeholder map. Real values live in local `.env` (gitignored) or GitHub Secrets / a private vault.
3. Runtime SQLite and other local state belong under `data/` which is gitignored except `data/.gitkeep`.
4. If a secret was ever committed, **rotate it immediately** and treat history as untrusted until rewritten.

## Authority boundary
This software operates within the Mermicorn Grove federation.

| Actor | May act |
|-------|---------|
| Cherry (operator) | Full |
| Authorized Mermicorn services | Per contract |

## Data classification
| Data | Classification |
|------|----------------|
| Public source / docs | Public |
| API keys, tokens | Private — never in git |
| User / commerce records | Private |
| Local `*.db` | Private / local only |

## P0 incident (2026-08-09)
Committed runtime DBs and `.env.ai` were removed from `main`. `.env.ai` contained **placeholder** key patterns only (not live credentials), but the habit was wrong. If any real keys were ever substituted locally and pushed, rotate them now.

## History note
Deleting files from `main` does not erase them from older commits. For full history purge use `git filter-repo` / BFG on a local clone with write access, then force-push only after coordination.
