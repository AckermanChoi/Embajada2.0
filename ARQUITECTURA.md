# Arquitectura: Backend vs Frontend

Tu proyecto **NO es un monolito** porque backend y frontend están en **puertos diferentes** y son **aplicaciones independientes**.

---

## 🚀 Cómo iniciar

**Backend (Puerto 8000):**
```powershell
.\start_backend.ps1
```

**Frontend (Puerto 5173):**
```powershell
.\start_frontend.ps1
```

---

## 📊 Diferencias

| Aspecto | Backend | Frontend |
|---------|---------|----------|
| **Lenguaje** | Python | JavaScript |
| **Framework** | FastAPI | React |
| **Puerto** | 8000 | 5173 |
| **Servidor** | Uvicorn | Vite |
| **Dependencias** | requirements.txt | package.json |

---

## 🔗 Comunicación

Frontend hace peticiones HTTP al Backend.

Backend permite acceso con **CORS**:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## ✅ Pruebas

- **Solo Backend**: ✅ http://localhost:8000/docs funciona
- **Solo Frontend**: ✅ Carga pero sin datos
- **Ambos**: ✅ Todo funciona

---

## 🎓 ¿Por qué NO es monolito?

✅ Puertos diferentes (8000 ≠ 5173)
✅ Lenguajes diferentes (Python ≠ JavaScript)
✅ Procesos independientes
✅ Dependencias separadas
✅ Se despliegan por separado
