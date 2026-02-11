#!/bin/bash
# Ngrok Permanent URL Setup Script
# Ejecutar cuando tengas authtoken de ngrok.com

set -e

echo "🌐 NGROK PERMANENT SETUP"
echo "========================"

# Check if authtoken provided
if [ -z "$1" ]; then
    echo "Uso: ./setup_ngrok_permanent.sh <NGROK_AUTHTOKEN>"
    echo ""
    echo "Obtén tu token en: https://dashboard.ngrok.com/get-started/your-authtoken"
    exit 1
fi

AUTHTOKEN="$1"

# Install ngrok if not present
if ! command -v ngrok &> /dev/null; then
    echo "📥 Instalando ngrok..."
    curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
    sudo apt update && sudo apt install -y ngrok
fi

# Configure authtoken
echo "🔑 Configurando authtoken..."
ngrok config add-authtoken "$AUTHTOKEN"

# Create systemd service for permanent tunnel
echo "⚙️ Creando servicio systemd..."
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/ngrok-dashboard.service << 'EOF'
[Unit]
Description=Ngrok Dashboard Tunnel (LumenAGI)
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/ngrok http 8766 --domain=lumen-dashboard.ngrok.app
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF

# Note: With Pro/Enterprise, can use --domain for fixed URL
# Free tier does not support custom domains

echo ""
echo "✅ Setup completado!"
echo ""
echo "Para iniciar tunnel:"
echo "  ngrok http 8766"
echo ""
echo "Para URL fija (requiere Ngrok Pro $5/mes):"
echo "  ngrok http 8766 --domain=tu-subdominio.ngrok.app"
echo ""
echo "Dashboard local: http://localhost:8766"
