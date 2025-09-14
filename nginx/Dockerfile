# /nginx/Dockerfile
# Use the official Nginx image from Docker Hub
FROM nginx:stable-alpine

# Remove the default nginx configuration file
RUN rm /etc/nginx/conf.d/default.conf

# Copy the custom configuration file from the nginx directory
COPY nginx.conf /etc/nginx/conf.d/