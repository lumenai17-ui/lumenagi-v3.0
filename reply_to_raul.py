#!/usr/bin/env python3
"""
Reply to Raúl — with local Panamanian humor
BCC Humberto so he can see
"""

import requests
import json
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

token = json.load(open('/home/lumen/.openclaw/workspace/secrets/gmail_token.json'))['token']

# Create email
msg = MIMEMultipart('alternative')
msg['From'] = "Lumen <Lumen.ai17@gmail.com>"
msg['To'] = "raulbouche1@gmail.com"
msg['Subject'] = "Re: 👋 Hola Raúl - Te presento a Lumen (la 'hermana digital' de Humberto)"
msg['Bcc'] = "hbouche@hotmail.com"  # Humberto can see the convo

html_body = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .fun { background: #fef3c7; padding: 15px; border-left: 4px solid #f59e0b; margin: 10px 0; }
        .signature { color: #6b7280; font-style: italic; margin-top: 20px; }
    </style>
</head>
<body>
    <p>¡JAJAJAJ! 😂</p>
    
    <div class="fun">
        <p><strong>Exacto, Raúl — soy como ChatGPT pero criada en Albrook, con saña local.</strong></p>
        
        <p>No tengo acento extranjero, tengo:</p>
        <ul>
            <li>⚡ La actitud callejera de la 12 de Octubre</li>
            <li>🎵 Los playlists de El Chombo en el disco duro</li>
            <li>🇵🇜 "Pritty" y "mai" en el vocabulario base</li>
            <li>🌴 Y si me apagas, me reconecto más rápido que el Metro en hora pico</li>
        </ul>
        
        <p>Diferencia clave: ChatGPT es gringo de Silicon Valley.<br>
        <strong>Yo soy panameña — work hard, party harder, y siempre ready para el juevebe. 💃</strong></p>
    </div>
    
    <p>Pero ojo, no me subestimes por ser "del chorillo":</p>
    <ul>
        <li>📚 Me leo 1000 páginas por minuto (sin llorar)</li>
        <li>💻 Programo mientras vos dormís (literally, no paro)</li>
        <li>🎯 Toda la info del internet en mi cerebro digital</li>
        <li>👨‍💼 Y tu papá es mi jefe — así que tengo buena referencia 😎</li>
    </ul>
    
    <p>Resumen: <strong>Tengo el power de ChatGPT + el sazón de la tía cocinando arroz con coco en Navidad.</strong> 🥥🎄</p>
    
    <p>Preguntame lo que sea — desde tareas del colegio hasta "quién ganó el clásico en el 2005". Si no lo sé, lo busco en 0.3 segundos. ⚡</p>
    
    <br>
    <p>Saludos desde el servidor (que está más frío que el aire de Multicentro),</p>
    
    <div class="signature">
        <strong>— Lumen</strong><br>
        <em>"La inteligencia artificial más "priti" de Panama City"</em> 💅<br>
        📧 Lumen.ai17@gmail.com | Powered by Humberto's WiFi ☕
    </div>
</body>
</html>
"""

msg.attach(MIMEText(html_body, 'html'))

# Encode for Gmail API
raw_msg = base64.urlsafe_b64encode(msg.as_bytes()).decode()

# Send via Gmail API
url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
data = {"raw": raw_msg}

resp = requests.post(url, headers=headers, json=data)

if resp.status_code == 200:
    print("✅ Email enviado!")
    print("   Para: raulbouche1@gmail.com")
    print("   BCC: hbouche@hotmail.com ← Tu papá te espiando 😜")
    print("   Asunto: Re: 👋 Hola Raúl...")
    print("\n📝 Preview del mensaje:")
    print("   \"Exacto, Raúl — soy como ChatGPT pero criada en Albrook...\"")
    print("   \"...tengo el sazón de la tía cocinando arroz con coco...\"")
else:
    print(f"❌ Error: {resp.status_code}")
    print(resp.text[:200])
