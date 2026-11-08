
FROM nginx:alpine

# Copy frontend files into Nginx's web root
COPY . /usr/share/nginx/html

# Replace the default Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
