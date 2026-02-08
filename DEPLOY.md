# DEPLOY.md - Guia de Deploy y QA

## Arquitectura de Deploy (Git-based)

```
Tu workspace (donde escribis):
  /home/node/workspace/public/    ← repo git (openclaw-site)

Cuando haces git push:
  GitHub webhook → auto-deploy → nginx sirve en ~5 segundos

Website publico:
  https://back.pulpouplatform.com/
```

### Como funciona (NUEVO - Git deploy)
- El directorio `public/` es un repo Git clonado de `github.com/opclawd/openclaw-site`
- Para publicar cambios: `git add -A && git commit -m "msg" && git push origin main`
- Un webhook de GitHub dispara el auto-deploy al servidor
- Los cambios aparecen en el website en ~5 segundos
- **NO usar rsync, scp, ni copiar manualmente**

### Workflow de deploy
```bash
# 1. Hacer cambios en public/
# 2. Verificar con smoke test
bash tools/smoke-test.sh

# 3. Si pasa, hacer deploy
cd /home/node/workspace/public
git add -A
git commit -m "descripcion del cambio"
git push origin main

# 4. Verificar que el deploy funciono (~5 seg despues)
curl -s -o /dev/null -w "%{http_code}" http://clawdbot-web/clawdbot/
```

### Paths importantes
| Lo que escribis | URL en la web |
|---|---|
| `public/clawdbot/index.html` | `https://back.pulpouplatform.com/clawdbot/` |
| `public/clawdbot/projects/index.json` | `https://back.pulpouplatform.com/clawdbot/projects/index.json` |
| `public/clawdbot/projects/test-N/index.html` | `https://back.pulpouplatform.com/clawdbot/projects/test-N/` |
| `public/index.html` | `https://back.pulpouplatform.com/` |

## QA Obligatorio - NUNCA digas "listo" sin verificar

### Pre-flight check (OBLIGATORIO antes de git push)
```bash
# Smoke test rapido (< 5 segundos)
bash tools/smoke-test.sh

# QA completo con reporte HTML
python3 tools/qa-check.py --report

# QA completo + auto-fix de errores comunes
python3 tools/qa-check.py --fix --report
```

### Verificacion manual minima
```bash
# 1. Verificar que el archivo existe localmente
ls -la public/clawdbot/projects/test-N/index.html

# 2. Verificar contenido no vacio
wc -c public/clawdbot/projects/test-N/index.html

# 3. Hacer deploy con git
cd /home/node/workspace/public
git add -A
git commit -m "agregar test-N"
git push origin main

# 4. Esperar deploy (~5 segundos)
sleep 6

# 5. Verificar HTTP 200 desde el website
curl -s -o /dev/null -w "%{http_code}" http://clawdbot-web/clawdbot/projects/test-N/index.html

# 6. Verificar que el HTML tiene contenido real
curl -s http://clawdbot-web/clawdbot/projects/test-N/index.html | head -5

# 7. Verificar index.json tiene la entrada
cat public/clawdbot/projects/index.json | jq length
```

### Regla de oro
**NUNCA reportes "terminado" o "todo bien" sin haber ejecutado `bash tools/smoke-test.sh` primero.**
Si el smoke test falla, arregla los errores y volve a correrlo hasta que pase.
**SIEMPRE hacer git push despues de modificar archivos en public/.**

## Errores comunes y como arreglarlos

### 404 en una pagina
- Causa: El archivo no existe o tiene mal el path
- Fix: Verificar que el archivo esta en `public/clawdbot/projects/test-N/index.html`
- NO en `public/projects/` directo

### index.json roto o vacio
- Causa: Escritura parcial o JSON invalido
- Fix: `cat public/clawdbot/projects/index.json | jq .` para validar
- Si falla: reconstruir leyendo los directorios existentes

### Pagina vacia (0 bytes)
- Causa: Error al escribir el archivo
- Fix: Regenerar el contenido del HTML

### Push falla (authentication)
- Causa: Token expirado o remote URL incorrecta
- Fix: Verificar `git remote -v` y que el token este en la URL
- El remote debe ser: `https://<token>@github.com/opclawd/openclaw-site.git`

### Push falla (conflict)
- Causa: Cambios remotos no integrados
- Fix: `git pull --rebase origin main` y luego reintentar push

## Como hacer HTTP requests para verificar
```bash
# Desde dentro del container, el website es accesible en:
curl http://clawdbot-web/clawdbot/
curl http://clawdbot-web/clawdbot/projects/index.json

# SIEMPRE verificar el status code:
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://clawdbot-web/clawdbot/projects/test-1/index.html)
if [ "$STATUS" != "200" ]; then
  echo "ERROR: test-1 returned $STATUS"
fi
```

## Checklist de calidad para paginas HTML
- [ ] DOCTYPE declarado
- [ ] `<html lang="es">`
- [ ] `<meta charset="UTF-8">`
- [ ] `<meta name="viewport">`
- [ ] `<title>` descriptivo
- [ ] Contenido real en `<body>` (no solo template)
- [ ] Estilos inline o en `<style>` (no deps externas que puedan fallar)
- [ ] Links internos verificados
- [ ] Responsive design
- [ ] Paleta consistente: #ff6b35, #f7931e, #ffd23f sobre #0a0a0f
