#!/usr/bin/env bash

sudo cp conf/cilichong.service /etc/systemd/system/

sudo systemctl start cilichong
sudo systemctl enable cilichong
sudo systemctl status cilichong

sudo cp conf/cilichong.nginx /etc/nginx/sites-enabled/cilichong
sudo nginx -t

sudo ufw allow 'Nginx Full'

sudo certbot --nginx -d cilichong.xyz -d www.cilichong.xyz

sudo systemctl restart nginx

sudo ufw delete allow 'Nginx HTTP'