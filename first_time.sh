#!/bin/bash
# First Time Setup Script for LXC Container

set -e # Exit immediately if a command exits with a non-zero status

echo "Starting first-time setup..."

# 1. Update and install system dependencies if needed
# This is useful if the LXC image is very minimal
# sudo apt-get update && sudo apt-get install -y python3-venv python3-pip

# 2. Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# 3. Activate and install dependencies
echo "Installing/Updating requirements..."
source venv/bin/activate
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found."
fi

echo "Setup complete."

# 4. Create a systemd service to run start.sh on boot
echo "Configuring systemd service..."

cat <<EOF | sudo tee /etc/systemd/system/app.service
[Unit]
Description=Flask Application Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=/bin/bash $(pwd)/start.sh
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 5. Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable app.service
sudo systemctl start app.service

echo "Systemd service configured and started."
