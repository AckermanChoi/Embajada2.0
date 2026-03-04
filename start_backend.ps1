# Activar entorno virtual
& .\.venv\Scripts\Activate.ps1

# Iniciar Backend en puerto 8000
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
