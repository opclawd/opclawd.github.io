#!/bin/bash
# Script de instalacion automatica de WordPress
# Ejecutar despues de 'docker compose up -d'
# Este script corre dentro del contenedor de WordPress

set -e

echo "=== OpenClaw Sports WordPress Installer ==="
echo "Esperando que MySQL este listo..."
sleep 10

# Variables
SITE_TITLE="OpenClaw Sports"
ADMIN_USER="opclawd"
ADMIN_PASS="LLNfHH-TRHPup6oSz-MI7RiQ"
ADMIN_EMAIL="opclawd@gmail.com"
DB_NAME="wp_sports"

echo "Instalando WordPress..."
wp core install \
  --url="http://localhost:8080" \
  --title="$SITE_TITLE" \
  --admin_user="$ADMIN_USER" \
  --admin_password="$ADMIN_PASS" \
  --admin_email="$ADMIN_EMAIL" \
  --allow-root

echo "Configurando permalink structure..."
wp rewrite structure '/%postname%/' --hard --allow-root
wp rewrite flush --hard --allow-root

echo "Instalando tema deportivo oscuro..."
# Opcion 1: Astra (tiene templates deportivos)
wp theme install astra --activate --allow-root

# Opcion 2: Kadence (bueno para personalizacion)
# wp theme install kadence --activate --allow-root

# Opcion 3: OceanWP (versatil)
# wp theme install oceanwp --activate --allow-root

echo "Instalando plugins utiles..."
# WPForms para contacto
wp plugin install wpforms-lite --activate --allow-root

# Elementor para builder visual
wp plugin install elementor --activate --allow-root

echo "Configurando opciones del sitio..."
wp option update blogname "OpenClaw Sports" --allow-root
wp option update blogdescription "Digital creator & tech enthusiast. Building things with AI." --allow-root
wp option update timezone_string "America/Argentina/Buenos_Aires" --allow-root
wp option update date_format "j/m/Y" --allow-root

echo "Creando pagina de inicio..."
wp post create \
  --post_type=page \
  --post_title='Inicio' \
  --post_status=publish \
  --post_author=1 \
  --allow-root

echo "Configurando pagina de inicio..."
wp option update show_on_front 'page' --allow-root
wp option update page_on_front 2 --allow-root

echo "=== Instalacion completada ==="
echo "URL: http://localhost:8080"
echo "Admin: http://localhost:8080/wp-admin"
echo "Usuario: $ADMIN_USER"
echo ""
echo "Para instalar tema deportivo especifico, ejecutar:"
echo "wp theme install [nombre-tema] --activate --allow-root"
