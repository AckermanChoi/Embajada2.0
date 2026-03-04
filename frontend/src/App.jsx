import { useState, useEffect } from 'react'
import ResidentesList from './components/ResidentesList'
import ResidenteForm from './components/ResidenteForm'
import ConfirmModal from './components/ConfirmModal'
import './App.css'

function App() {
  const [residentes, setResidentes] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [showConfirm, setShowConfirm] = useState(false)
  const [residenteToDelete, setResidenteToDelete] = useState(null)
  const pageSize = 10

  const API_URL = 'http://localhost:8000'

  useEffect(() => {
    fetchResidentes()
  }, [])

  useEffect(() => {
    const totalPages = Math.max(1, Math.ceil(residentes.length / pageSize))
    if (page > totalPages) {
      setPage(totalPages)
    }
  }, [residentes, page, pageSize])

  const fetchResidentes = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_URL}/residentes`)
      if (!response.ok) throw new Error('Error al cargar residentes')
      const data = await response.json()
      setResidentes(data)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleAddNew = () => {
    setEditingId(null)
    setShowForm(true)
  }

  const handleEdit = (id) => {
    setEditingId(id)
    setShowForm(true)
  }

  const handleFormClose = () => {
    setShowForm(false)
    setEditingId(null)
  }

  const handlePageChange = (nextPage) => {
    if (nextPage < 1) return
    const totalPages = Math.max(1, Math.ceil(residentes.length / pageSize))
    if (nextPage > totalPages) return
    setPage(nextPage)
  }

  const handleFormSubmit = async (data) => {
    try {
      const method = editingId ? 'PUT' : 'POST'
      const url = editingId ? `${API_URL}/residentes/${editingId}` : `${API_URL}/residentes`
      
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })

      if (!response.ok) {
        let errorMessage = 'Error al guardar residente'
        try {
          const errorData = await response.json()
          if (errorData.detail) {
            // Si detail es string, lo usamos; si es objeto, lo convertimos
            errorMessage = typeof errorData.detail === 'string' 
              ? errorData.detail 
              : JSON.stringify(errorData.detail)
          } else if (errorData.message) {
            errorMessage = errorData.message
          }
        } catch (e) {
          // Si no puede parsear JSON, usa mensaje generado
          errorMessage = `Error del servidor (${response.status})`
        }
        throw new Error(errorMessage)
      }
      
      await fetchResidentes()
      handleFormClose()
    } catch (err) {
      setError(err.message)
    }
  }

  const handleDelete = (id) => {
    setResidenteToDelete(id)
    setShowConfirm(true)
  }

  const confirmDelete = async () => {
    try {
      const response = await fetch(`${API_URL}/residentes/${residenteToDelete}`, {
        method: 'DELETE'
      })
      if (!response.ok) {
        let errorMessage = 'Error al eliminar residente'
        try {
          const errorData = await response.json()
          if (errorData.detail) {
            errorMessage = typeof errorData.detail === 'string' 
              ? errorData.detail 
              : JSON.stringify(errorData.detail)
          } else if (errorData.message) {
            errorMessage = errorData.message
          }
        } catch (e) {
          errorMessage = `Error del servidor (${response.status})`
        }
        throw new Error(errorMessage)
      }
      await fetchResidentes()
    } catch (err) {
      setError(err.message)
    } finally {
      setShowConfirm(false)
      setResidenteToDelete(null)
    }
  }

  const cancelDelete = () => {
    setShowConfirm(false)
    setResidenteToDelete(null)
  }

  const handleLogoClick = () => {
    setShowForm(false)
    setEditingId(null)
    setPage(1)
  }

  const totalPages = Math.max(1, Math.ceil(residentes.length / pageSize))
  const pagedResidentes = residentes.slice(
    (page - 1) * pageSize,
    page * pageSize
  )

  return (
    <>
      <header className="header">
        <div className="brand" onClick={handleLogoClick} style={{ cursor: 'pointer' }}>
          <div className="logo-frame">
            <img
              src="images/escudo-de-nicaragua-logo-png_seeklogo-260075.png"
              alt="Escudo"
              loading="eager"
            />
          </div>
          <div className="brand-text">
            <p className="brand-eyebrow">Embajada</p>
            <h1>Gestion de Residentes</h1>
          </div>
        </div>
        <button className="btn-primary" onClick={handleAddNew}>
          Agregar Residente
        </button>
      </header>

      <main className="main-content">
        {error && <div className="error">{error}</div>}
        
        {showForm ? (
          <ResidenteForm
            residente={editingId ? residentes.find(r => r.id === editingId) : null}
            onSubmit={handleFormSubmit}
            onCancel={handleFormClose}
          />
        ) : (
          <>
            {loading ? (
              <div className="loading">Cargando...</div>
            ) : (
              <ResidentesList
                residentes={pagedResidentes}
                page={page}
                totalPages={totalPages}
                onPageChange={handlePageChange}
                onEdit={handleEdit}
                onDelete={handleDelete}
              />
            )}
          </>
        )}
      </main>

      <ConfirmModal
        isOpen={showConfirm}
        title="Confirmar eliminación"
        message="¿Está seguro de que desea eliminar este residente? Esta acción no se puede deshacer."
        onConfirm={confirmDelete}
        onCancel={cancelDelete}
      />
    </>
  )
}

export default App
