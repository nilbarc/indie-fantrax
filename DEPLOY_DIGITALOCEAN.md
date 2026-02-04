# Deploying Indie Fantrax on DigitalOcean

This guide uses a $6/month Droplet with Ubuntu.

## 1. Create a Droplet

1. Log into DigitalOcean
2. Create Droplet → Ubuntu 22.04 → Basic → $6/month (1GB RAM)
3. Add your SSH key
4. Create and note the IP address

## 2. Connect and Install Dependencies

```bash
ssh root@YOUR_DROPLET_IP

# Update system
apt update && apt upgrade -y

# Install Python and PostgreSQL
apt install -y python3-pip python3-venv postgresql postgresql-contrib nginx
```

## 3. Set Up PostgreSQL

```bash
# Switch to postgres user and create database
sudo -u postgres psql

# In the postgres prompt:
CREATE DATABASE indie_fantrax;
CREATE USER fantrax WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE indie_fantrax TO fantrax;
\q
```

## 4. Create App User and Deploy Code

```bash
# Create a user for the app
useradd -m -s /bin/bash fantrax
cd /home/fantrax

# Clone your repo (or copy files)
git clone YOUR_REPO_URL app
# OR: scp -r indie-fantrax/* root@YOUR_IP:/home/fantrax/app/

cd app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set ownership
chown -R fantrax:fantrax /home/fantrax/app
```

## 5. Configure Environment

```bash
# Create .env file
cat > /home/fantrax/app/.env << 'EOF'
DATABASE_URL=postgresql://fantrax:your_secure_password@localhost:5432/indie_fantrax
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
ACCESS_CODE=your_secret_code
TIMEZONE=Europe/London
EOF

chmod 600 /home/fantrax/app/.env
chown fantrax:fantrax /home/fantrax/app/.env
```

## 6. Create Systemd Service

```bash
cat > /etc/systemd/system/fantrax.service << 'EOF'
[Unit]
Description=Indie Fantrax
After=network.target postgresql.service

[Service]
User=fantrax
WorkingDirectory=/home/fantrax/app
Environment=PATH=/home/fantrax/app/venv/bin
ExecStart=/home/fantrax/app/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
systemctl daemon-reload
systemctl enable fantrax
systemctl start fantrax

# Check status
systemctl status fantrax
```

## 7. Set Up Nginx (Optional but Recommended)

```bash
cat > /etc/nginx/sites-available/fantrax << 'EOF'
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

ln -s /etc/nginx/sites-available/fantrax /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
```

## 8. Test It

Visit `http://YOUR_DROPLET_IP` in your browser. You should see the submission form.

Test the Telegram posting:
```bash
curl -X POST http://YOUR_DROPLET_IP/api/trigger-post
```

## Useful Commands

```bash
# View logs
journalctl -u fantrax -f

# Restart after code changes
systemctl restart fantrax

# Check if running
systemctl status fantrax
```

## Optional: Add HTTPS with Let's Encrypt

```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d yourdomain.com
```
