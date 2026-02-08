# DEPLOY.md - Guia de Deploy y QA

## Arquitectura de Deploy

```
Tu workspace (donde escribis):
  /home/node/.openclaw/workspace/public/clawdbot/

Se sincroniza automaticamente cada 10s a:
  /home/node/workspace/public/clawdbot/

Que es servido por nginx en:
  https://back.pulpouplatform.com/clawdbot/
```

### Como funciona
- Un script de rsync externo copia TODO lo que pongas en `public/` a la carpeta del website cada 10 segundos
- NO necesitas hacer deploy manual, ni rsync, ni scp
- Solo escribi archivos en `public/clawdbot/` y aparecen solos en la web
- El website se sirve desde el container `clawdbot-web` en el mismo Docker network

### Paths importantes
| Lo que escribis | URL en la web |
|---|---|
| `public/clawdbot/index.html` | `https://back.pulpouplatform.com/clawdbot/` |
| `public/clawdbot/projects/index.json` | `https://back.pulpouplatform.com/clawdbot/projects/index.json` |
| `public/clawdbot/projects/test-N/index.html` | `https://back.pulpouplatform.com/clawdbot/projects/test-N/` |

## QA Obligatorio - NUNCA digas "listo" sin verificar

### Pre-flight check (OBLIGATORIO antes de reportar exito)
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

# 3. Esperar sync (10 segundos)
sleep 12

# 4. Verificar HTTP 200 desde el website
curl -s -o /dev/null -w "%{http_code}" http://clawdbot-web/clawdbot/projects/test-N/index.html

# 5. Verificar que el HTML tiene contenido real
curl -s http://clawdbot-web/clawdbot/projects/test-N/index.html | head -5

# 6. Verificar index.json tiene la entrada
cat public/clawdbot/projects/index.json | jq length
```

### Regla de oro
**NUNCA reportes "terminado" o "todo bien" sin haber ejecutado `bash tools/smoke-test.sh` primero.**
Si el smoke test falla, arregla los errores y volve a correrlo hasta que pase.

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

### Sync no funciona
- Causa: Permisos incorrectos
- Fix: Los archivos deben ser de tu usuario (UID 1000)
- Verificar: `ls -la public/clawdbot/`

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
