#!/usr/bin/env bash

# Add Certbot PPA
sudo apt-get update
sudo apt-get install software-properties-common
sudo add-apt-repository universe
sudo add-apt-repository ppa:certbot/certbot
sudo apt-get update

# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

sudo certbot --nginx -d cilichong.xyz -d www.cilichong.xyz

sudo ufw delete allow 'Nginx HTTP'
