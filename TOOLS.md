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

### QA & Testing Tools
- **Smoke test** → `bash tools/smoke-test.sh` (< 5 seg, verificación rápida)
- **QA completo** → `python3 tools/qa-check.py --report` (full audit con HTML report)
- **QA + auto-fix** → `python3 tools/qa-check.py --fix --report` (arregla errores comunes)

---

## Git Configuration
- **user.name:** openclaw
- **user.email:** opclawd@gmail.com
- **credential.helper:** store (token in ~/.git-credentials)

---

## Deploy con Git (NUEVO - reemplaza rsync)

### Cómo publicar cambios al website
```bash
cd /home/node/workspace/public
git add -A
git commit -m "descripción del cambio"
git push origin main
```
El webhook de GitHub dispara auto-deploy. Los cambios aparecen en ~5 segundos.

### Reglas de deploy
- SIEMPRE hacer git push después de modificar archivos en public/
- SIEMPRE verificar con `bash tools/smoke-test.sh` ANTES del push
- Commit messages descriptivos en español
- NO usar rsync ni copiar manualmente

### Estructura del repo
```
public/
├── clawdbot/
│   ├── index.html        (panel de proyectos)
│   ├── projects/          (resultados de tests)
│   │   ├── index.json     (índice)
│   │   └── test-N/        (cada test)
│   ├── viz/               (visualizaciones)
│   ├── downloads/         (archivos descargados)
│   ├── apps/              (aplicaciones)
│   └── reports/           (reportes)
├── index.html             (homepage principal)
└── ...
```

### Verificación HTTP desde el container
```bash
# El website es accesible internamente en:
curl -s -o /dev/null -w "%{http_code}" http://clawdbot-web/clawdbot/
curl -s -o /dev/null -w "%{http_code}" http://clawdbot-web/clawdbot/projects/index.json
curl -s -o /dev/null -w "%{http_code}" http://clawdbot-web/clawdbot/projects/test-1/index.html
```

### Paths importantes
| Lo que escribís | URL pública |
|---|---|
| `public/clawdbot/index.html` | `https://back.pulpouplatform.com/clawdbot/` |
| `public/clawdbot/projects/index.json` | `https://back.pulpouplatform.com/clawdbot/projects/index.json` |
| `public/clawdbot/projects/test-N/index.html` | `https://back.pulpouplatform.com/clawdbot/projects/test-N/` |

---

## Paths (Workspace-relative)
- Exports: `exports/`
- Scripts: `scripts/`
- Apps: `apps/`
- Public web: `public/clawdbot/`
- Projects index: `public/clawdbot/projects/index.json`
- Project pages: `public/clawdbot/projects/test-N/index.html`
- QA tools: `tools/`

---

## REGLA DE ORO - QA OBLIGATORIO

**NUNCA reportes "terminado" o "todo funciona" sin verificar:**

```bash
# 1. Ejecutar smoke test (OBLIGATORIO antes de reportar éxito)
bash tools/smoke-test.sh

# 2. Si falla algo, correr QA completo con auto-fix:
python3 tools/qa-check.py --fix --report --verbose

# 3. Verificación HTTP manual mínima:
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://clawdbot-web/clawdbot/projects/test-N/index.html)
if [ "$STATUS" != "200" ]; then echo "ERROR: HTTP $STATUS"; fi

# 4. Verificar que el HTML tiene contenido real (no está vacío):
SIZE=$(wc -c < public/clawdbot/projects/test-N/index.html)
if [ "$SIZE" -lt 100 ]; then echo "ERROR: archivo vacío o muy pequeño"; fi
```

**Si el smoke test falla, arreglá los errores y volvé a correrlo hasta que pase. NUNCA ignorar fallos.**

---
*Last updated: 2026-02-08*
