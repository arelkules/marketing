# notebooklm-sync

Sync NotebookLM notebooks to the agent brain (backend knowledge base).

## What this does

Runs `notebooklm_sync.py` — opens NotebookLM using saved Google cookies, extracts
knowledge from the configured notebooks via AI chat, then uploads each notebook's
content to the backend at `http://localhost:8000/ingest/upload`.

## Usage

```
/notebooklm-sync
```

Run the sync script:

```bash
cd /home/user/marketing && python notebooklm_sync.py
```

After running, check the output:
- `✅ Uploaded to agents` — the notebook was sent to the backend successfully
- `📁 Saved locally: notebooklm_export/<file>.txt` — backend was unreachable; upload
  these files manually via the dashboard at `/knowledge`

## Configuration (in notebooklm_sync.py)

| Variable | Purpose |
|---|---|
| `BACKEND_URL` | Where to POST extracted content (default: `http://localhost:8000`) |
| `TARGET_NOTEBOOKS` | List of notebook name substrings to sync; `[]` = all |
| `COOKIES` | Google session cookies for authentication |
| `EXTRACTION_PROMPTS` | Questions sent to each notebook's AI chat |

## Requirements

- Python packages: `playwright`, `requests`
- Chromium binary at `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`
