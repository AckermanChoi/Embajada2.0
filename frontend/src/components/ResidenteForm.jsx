import { useState, useEffect } from 'react'

function ResidenteForm({ residente, onSubmit, onCancel }) {
  const [formData, setFormData] = useState({
    nombre: '',
    apellido: '',
    fecha_nacimiento: '',
    pasaporte: '',
    email: '',
    telefono: '',
    direccion: '',
    ocupacion: '',
    estado_civil: ''
  })

  const [errors, setErrors] = useState({})

  useEffect(() => {
    if (residente) {
      setFormData(residente)
    }
  }, [residente])

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    // Limpiar error del campo
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[name]
        return newErrors
      })
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    try {
      await onSubmit(formData)
    } catch (err) {
      if (err.response?.data?.detail) {
        setErrors({ submit: err.response.data.detail })
      } else {
        setErrors({ submit: 'Error al guardar' })
      }
    }
  }

  return (
    <div className="form-container">
      <h2>{residente ? 'Editar Residente' : 'Nuevo Residente'}</h2>
      
      {errors.submit && <div className="error">{errors.submit}</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="nombre">Nombres *</label>
          <input
            type="text"
            id="nombre"
            name="nombre"
            value={formData.nombre}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="apellido">Apellidos *</label>
          <input
            type="text"
            id="apellido"
            name="apellido"
            value={formData.apellido}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="fecha_nacimiento">Fecha de Nacimiento *</label>
          <input
            type="date"
            id="fecha_nacimiento"
            name="fecha_nacimiento"
            value={formData.fecha_nacimiento}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="pasaporte">Pasaporte *</label>
          <input
            type="text"
            id="pasaporte"
            name="pasaporte"
            value={formData.pasaporte}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="email">Email *</label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="telefono">Teléfono</label>
          <input
            type="tel"
            id="telefono"
            name="telefono"
            value={formData.telefono}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label htmlFor="direccion">Dirección</label>
          <input
            type="text"
            id="direccion"
            name="direccion"
            value={formData.direccion}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label htmlFor="ocupacion">Ocupación</label>
          <input
            type="text"
            id="ocupacion"
            name="ocupacion"
            value={formData.ocupacion}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label htmlFor="estado_civil">Estado Civil</label>
          <select
            id="estado_civil"
            name="estado_civil"
            value={formData.estado_civil}
            onChange={handleChange}
          >
            <option value="">Seleccionar...</option>
            <option value="Soltero">Soltero</option>
            <option value="Soltera">Soltera</option>
            <option value="Casado">Casado</option>
            <option value="Casada">Casada</option>
            <option value="Divorciado">Divorciado</option>
            <option value="Divorciada">Divorciada</option>
            <option value="Viudo">Viudo</option>
            <option value="Viuda">Viuda</option>
            <option value="Unión Libre">Unión Libre</option>
          </select>
        </div>

        <div className="form-actions">
          <button type="button" className="btn-secondary" onClick={onCancel}>
            Cancelar
          </button>
          <button type="submit" className="btn-primary">
            {residente ? 'Guardar Cambios' : 'Guardar'}
          </button>
        </div>
      </form>
    </div>
  )
}

export default ResidenteForm
