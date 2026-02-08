#!/bin/bash
# Instalacion via curl y API REST (alternativa a WP-CLI)
# Ejecutar despues de que WordPress este corriendo

echo "=== Instalacion WordPress via curl ==="

WP_URL="http://localhost:8080"
ADMIN_USER="opclawd"
ADMIN_PASS="LLNfHH-TRHPup6oSz-MI7RiQ"
ADMIN_EMAIL="opclawd@gmail.com"
SITE_TITLE="OpenClaw Sports"

# Esperar a que WordPress responda
echo "Esperando que WordPress inicie..."
for i in {1..30}; do
  if curl -s "$WP_URL/wp-admin/install.php" > /dev/null; then
    echo "WordPress listo!"
    break
  fi
  echo "Intento $i/30..."
  sleep 2
done

# La instalacion web requiere interaccion con el formulario de instalacion
# Este script abre el instalador en navegador

echo ""
echo "Abriendo instalador de WordPress..."
echo "URL: $WP_URL/wp-admin/install.php"
echo ""
echo "Datos para completar:"
echo "  - Titulo del sitio: $SITE_TITLE"
echo "  - Usuario: $ADMIN_USER"
echo "  - Password: $ADMIN_PASS"
echo "  - Email: $ADMIN_EMAIL"

# Intentar abrir con chromium si esta disponible
if command -v /usr/bin/chromium &> /dev/null; then
  /usr/bin/chromium --no-sandbox "$WP_URL/wp-admin/install.php" &
else
  echo "Chromium no disponible. Abrir manualmente el URL."
fi
