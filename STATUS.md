# Status

**State:** BUILDING (hygiene pass applied)  
**Last updated:** 2026-08-09

## P0 complete on main
- Hardened `.gitignore` (`.env*`, `*.db*`, `data/`, caches)
- Removed `.env.ai`, `mermicorn.db`, and all tracked `data/*.db*` from tree
- Left `data/.gitkeep` so the directory exists without runtime files
- SECURITY.md updated with rotate/history guidance

## Still true
- Large Python commerce stack exists (`api.py`, `src/commerce_ai/*`, Docker/deploy configs)
- Public code only; private data stays local or vaulted

## Operator TODO
1. Rotate any real keys if they were ever present outside placeholders
2. Optional: history rewrite to purge old blobs
3. Keep using `.env.template` + GitHub Secrets only
