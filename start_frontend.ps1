# CD a la carpeta frontend
cd frontend

# Instalar dependencias si no existen
if (-not (Test-Path "node_modules")) {
    npm install
}

# Iniciar servidor de desarrollo
npm run dev
