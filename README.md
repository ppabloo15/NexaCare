# NexaCare — Sistema de Triaje Médico con IA

Aplicación web de triaje médico desarrollada con Streamlit y Claude API.  
TFG · SMR · 2025-2026

---

## Requisitos

- Python 3.10 o superior
- Las dependencias del proyecto (ver `requirements.txt`)

## Instalación

```bash
pip install -r requirements.txt
```

## Configuración

Crea el archivo `.streamlit/secrets.toml` con tus claves API:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."   # Obligatorio para IA real
GROQ_API_KEY      = "gsk_..."      # Opcional (fallback gratuito)

NEXACARE_GMAIL_USER = "tu@gmail.com"     # Opcional: envío de informes por email
NEXACARE_GMAIL_PASS = "app-password"     # Contraseña de aplicación de Gmail

NEXACARE_PIN = "1234"                    # PIN de acceso al panel admin (4 dígitos)
NEXACARE_URL = "http://localhost:8501"   # URL pública de la app (para QR en PDF)
```

> Sin `ANTHROPIC_API_KEY` la app funciona igualmente en modo demo con respuestas predefinidas.

## Ejecución

**Windows:** doble clic en `INICIAR NEXACARE.bat`

**Manual:**
```bash
python -m streamlit run app.py
```

La app se abre en `http://localhost:8501`

## Estructura del proyecto

```
app.py              # Aplicación principal (UI y navegación)
logica_triaje.py    # Lógica de puntuación y niveles de urgencia
ai_service.py       # Integración con Claude API y Groq
database.py         # Base de datos SQLite
pdf_report.py       # Generación de informes PDF
email_service.py    # Envío de informes por correo
hospital_finder.py  # Búsqueda de centros sanitarios cercanos
tests/              # PDFs de prueba generados durante el desarrollo
```

## Panel de administración

Accede desde la pantalla principal → "Acceso personal sanitario".  
Introduce el PIN configurado en `secrets.toml` (por defecto: `6825`).

## Niveles de triaje

| Nivel | Color | Rango | Acción |
|-------|-------|-------|--------|
| VERDE | 🟢 | 0–24% | Cuidados en casa |
| AMARILLO | 🟡 | 25–44% | Centro de salud hoy |
| NARANJA | 🟠 | 45–69% | Urgencias hospitalarias |
| ROJO | 🔴 | 70–100% | Llamar al 112 |
