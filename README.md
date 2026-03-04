# Sistema de Gestión de Residentes


Backend y Frontend separados en **puertos diferentes**.

---

## 🚀 Inicio Rápido

**Terminal 1 - Backend (Puerto 8000):**
```powershell
cd embajada
.\start_backend.ps1
```
→ http://localhost:8000/docs

**Terminal 2 - Frontend (Puerto 5173):**
```powershell
cd embajada
.\start_frontend.ps1
```
→ http://localhost:5173

---

## 📁 Estructura

```
embajada/
├── backend/         FastAPI (Puerto 8000)
├── frontend/        React + Vite (Puerto 5173)
├── docs/            Scripts SQL
├── tests/           Tests
└── .venv/           Python virtualenv
```

---

## ✅ Requisitos

- Python 3.8+
- Node.js 16+
- MySQL
