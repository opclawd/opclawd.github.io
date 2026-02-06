# Usar imagen oficial de Nginx Alpine (ligera)
FROM nginx:alpine

# Eliminar configuración y archivos por defecto
RUN rm -rf /usr/share/nginx/html/* /etc/nginx/conf.d/*

# Copiar archivos estáticos de la app
COPY . /usr/share/nginx/html

# Copiar configuración personalizada de Nginx
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# Exponer puerto 80
EXPOSE 80

# Iniciar Nginx en foreground
CMD ["nginx", "-g", "daemon off;"]
