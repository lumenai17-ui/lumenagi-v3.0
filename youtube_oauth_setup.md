# YouTube Analytics OAuth Setup — Instructions

## Paso a Paso (Con Humberto en PC)

### 1. Google Cloud Console
- Ir a: https://console.cloud.google.com/
- Login con: Lumen.ai17@gmail.com

### 2. Crear Proyecto
- Click "Create Project"
- Nombre: `lumen-youtube-analytics`
- Click "Create"

### 3. Habilitar YouTube Data API v3
- APIs & Services → Library
- Buscar: "YouTube Data API v3"
- Click "Enable"

### 4. Crear OAuth Credentials
- APIs & Services → Credentials
- "Create Credentials" → "OAuth client ID"
- Tipo: "Desktop application"
- Nombre: "LumenAGI Desktop"
- Download JSON → guardar como `secrets/youtube_credentials.json`

### 5. Configurar Consent Screen (si pide)
- OAuth consent screen → External
- App name: "LumenAGI Analytics"
- User support email: Lumen.ai17@gmail.com
- Developer contact: Lumen.ai17@gmail.com
- Scopes: `https://www.googleapis.com/auth/youtube.readonly`

### 6. Autorización ( yo hago con browser control )
- Yo ejecuto `youtube_analytics_client.py --auth`
- Genera URL de autorización
- Humberto abre URL y da permiso
- Copia código de vuelta a mí
- Guardo refresh_token

## API Quotas (Gratis)
- 10,000 units/day
- 1 video view = 1 unit
- Suficiente para analytics diarios

## Archivos Resultantes
```
secrets/
├── youtube_credentials.json      (client_id, client_secret)
└── youtube_token.json            (refresh_token, access_token)
```

---
*Ready for execution when Humberto at PC*
