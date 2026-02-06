# TOOLS.md - Local Notes

Environment-specific tools and configurations for this OpenClaw instance.

---

## Available Tools

### Browsers
- **Chromium** → `/usr/bin/chromium --no-sandbox`

### Programming Languages
- **Python 3** → with `requests`, `urllib`, `json`, `csv`, `sqlite3`, `xml.etree`, `smtplib`, `email.mime`

### Shell & Utilities
- **bash** → standard shell
- **curl** → HTTP requests
- **jq** → JSON processing
- **git** → version control

### Databases
- **SQLite3** → local database engine

### APIs & Services
- **GitHub API** → via curl with token auth
- **Telegram Bot API** → for messaging
- **Gmail SMTP** → `smtp.gmail.com:587`

---

## Git Configuration
- **user.name:** openclaw
- **user.email:** opclawd@gmail.com
- **credential.helper:** store (token in ~/.git-credentials)

---

## Paths (Workspace-relative)
- Exports: `exports/`
- Scripts: `scripts/`
- Apps: `apps/`
- Public web: `public/`
- Projects: `public/projects/`

---
*Last updated: 2026-02-06*
