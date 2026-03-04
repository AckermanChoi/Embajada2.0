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
  const [touched, setTouched] = useState({})

  // Reglas de validación (sincronizadas con backend)
  const validationRules = {
    nombre: [
      { test: v => (v || '').trim().length > 0, message: 'Campo requerido' },
      { test: v => (v || '').trim().length >= 2, message: 'Debe tener al menos 2 caracteres' },
      { test: v => (v || '').trim().length <= 100, message: 'No puede exceder 100 caracteres' },
      { test: v => !(v || '') || /^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$/.test(v), message: 'Solo se permiten letras y espacios' }
    ],
    apellido: [
      { test: v => (v || '').trim().length > 0, message: 'Campo requerido' },
      { test: v => (v || '').trim().length >= 2, message: 'Debe tener al menos 2 caracteres' },
      { test: v => (v || '').trim().length <= 100, message: 'No puede exceder 100 caracteres' },
      { test: v => !(v || '') || /^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$/.test(v), message: 'Solo se permiten letras y espacios' }
    ],
    pasaporte: [
      { test: v => (v || '').trim().length > 0, message: 'Campo requerido' },
      { test: v => (v || '').trim().length >= 6, message: 'Debe tener al menos 6 caracteres' },
      { test: v => (v || '').trim().length <= 50, message: 'No puede exceder 50 caracteres' }
    ],
    email: [
      { test: v => (v || '').trim().length > 0, message: 'Campo requerido' },
      { test: v => !(v || '') || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v), message: 'Correo electrónico inválido' }
    ],
    fecha_nacimiento: [
      { test: v => v.length > 0, message: 'Campo requerido' },
      { test: v => {
        if (!v) return false
        const date = new Date(v)
        return date <= new Date()
      }, message: 'La fecha de nacimiento no puede ser futura' },
      { test: v => {
        if (!v) return false
        const today = new Date()
        const birthDate = new Date(v)
        const edad = today.getFullYear() - birthDate.getFullYear()
        return edad <= 150
      }, message: 'La fecha de nacimiento no es válida' }
    ],
    telefono: [
      { test: v => (v || '').trim().length > 0, message: 'Campo requerido' },
      { test: v => (v || '').trim().length >= 7, message: 'Debe tener al menos 7 caracteres' },
      { test: v => (v || '').trim().length <= 15, message: 'No puede exceder 15 caracteres' }
    ],
    direccion: [
      { test: v => (v || '').trim().length > 0, message: 'Campo requerido' },
      { test: v => (v || '').trim().length <= 255, message: 'No puede exceder 255 caracteres' }
    ],
    ocupacion: [
      { test: v => (v || '').trim().length > 0, message: 'Campo requerido' },
      { test: v => (v || '').trim().length <= 100, message: 'No puede exceder 100 caracteres' },
      { test: v => !(v || '') || /^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\.\-]+$/.test(v), message: 'Solo se permiten letras, espacios, puntos y guiones' }
    ],
    estado_civil: [
      { test: v => v.length > 0, message: 'Campo requerido' }
    ]
  }

  const validateField = (name, value) => {
    if (!validationRules[name]) return null
    
    for (const rule of validationRules[name]) {
      if (!rule.test(value)) {
        return rule.message
      }
    }
    return null
  }

  const validateForm = () => {
    const newErrors = {}
    
    // Validar todos los campos
    const allFields = ['nombre', 'apellido', 'fecha_nacimiento', 'pasaporte', 'email', 'telefono', 'direccion', 'ocupacion', 'estado_civil']
    
    allFields.forEach(field => {
      const fieldValue = formData[field]
      
      if (!fieldValue || (typeof fieldValue === 'string' && fieldValue.trim() === '')) {
        newErrors[field] = 'Campo requerido'
      } else {
        const error = validateField(field, fieldValue)
        if (error) newErrors[field] = error
      }
    })
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  useEffect(() => {
    if (residente) {
      // Convertir null values a strings vacíos para evitar problemas con validaciones
      const normalizedData = {
        nombre: residente.nombre || '',
        apellido: residente.apellido || '',
        fecha_nacimiento: residente.fecha_nacimiento || '',
        pasaporte: residente.pasaporte || '',
        email: residente.email || '',
        telefono: residente.telefono || '',
        direccion: residente.direccion || '',
        ocupacion: residente.ocupacion || '',
        estado_civil: residente.estado_civil || ''
      }
      setFormData(normalizedData)
    }
  }, [residente])

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    
    // Validar en tiempo real si el campo ha sido tocado
    if (touched[name]) {
      const error = validateField(name, value)
      setErrors(prev => {
        const newErrors = { ...prev }
        if (error) {
          newErrors[name] = error
        } else {
          delete newErrors[name]
        }
        return newErrors
      })
    }
  }

  const handleBlur = (e) => {
    const { name } = e.target
    setTouched(prev => ({
      ...prev,
      [name]: true
    }))
    
    const error = validateField(name, formData[name])
    setErrors(prev => {
      const newErrors = { ...prev }
      if (error) {
        newErrors[name] = error
      } else {
        delete newErrors[name]
      }
      return newErrors
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }
    
    try {
      await onSubmit(formData)
    } catch (err) {
      // El error ya se maneja en App.jsx
    }
  }

  return (
    <div className="form-container">
      <h2>{residente ? 'Editar Residente' : 'Nuevo Residente'}</h2>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="nombre">Nombres *</label>
          <input
            type="text"
            id="nombre"
            name="nombre"
            value={formData.nombre}
            onChange={handleChange}
            onBlur={handleBlur}
            className={errors.nombre ? 'error' : ''}
            required
          />
          {errors.nombre && <span className="field-error">{errors.nombre}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="apellido">Apellidos *</label>
          <input
            type="text"
            id="apellido"
            name="apellido"
            value={formData.apellido}
            onChange={handleChange}
            onBlur={handleBlur}
            className={errors.apellido ? 'error' : ''}
            required
          />
          {errors.apellido && <span className="field-error">{errors.apellido}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="fecha_nacimiento">Fecha de Nacimiento *</label>
          <input
            type="date"
            id="fecha_nacimiento"
            name="fecha_nacimiento"
            value={formData.fecha_nacimiento}
            onChange={handleChange}
            onBlur={handleBlur}
            className={errors.fecha_nacimiento ? 'error' : ''}
            required
          />
          {errors.fecha_nacimiento && <span className="field-error">{errors.fecha_nacimiento}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="pasaporte">Pasaporte *</label>
          <input
            type="text"
            id="pasaporte"
            name="pasaporte"
            value={formData.pasaporte}
            onChange={handleChange}
            onBlur={handleBlur}
            className={errors.pasaporte ? 'error' : ''}
            required
          />
          {errors.pasaporte && <span className="field-error">{errors.pasaporte}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="email">Email *</label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            onBlur={handleBlur}
            className={errors.email ? 'error' : ''}
            required
          />
          {errors.email && <span className="field-error">{errors.email}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="telefono">Teléfono *</label>
          <input
            type="tel"
            id="telefono"
            name="telefono"
            value={formData.telefono}
            onChange={handleChange}
            onBlur={handleBlur}
            className={errors.telefono ? 'error' : ''}
            required
          />
          {errors.telefono && <span className="field-error">{errors.telefono}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="direccion">Dirección *</label>
          <input
            type="text"
            id="direccion"
            name="direccion"
            value={formData.direccion}
            onChange={handleChange}
            onBlur={handleBlur}
            className={errors.direccion ? 'error' : ''}
            required
          />
          {errors.direccion && <span className="field-error">{errors.direccion}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="ocupacion">Ocupación *</label>
          <input
            type="text"
            id="ocupacion"
            name="ocupacion"
            value={formData.ocupacion}
            onChange={handleChange}
            onBlur={handleBlur}
            className={errors.ocupacion ? 'error' : ''}
            required
          />
          {errors.ocupacion && <span className="field-error">{errors.ocupacion}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="estado_civil">Estado Civil *</label>
          <select
            id="estado_civil"
            name="estado_civil"
            value={formData.estado_civil}
            onChange={handleChange}
            onBlur={handleBlur}
            className={errors.estado_civil ? 'error' : ''}
            required
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
          {errors.estado_civil && <span className="field-error">{errors.estado_civil}</span>}
        </div>

        <div className="form-actions">
          <button type="button" className="btn-secondary" onClick={onCancel}>
            Cancelar
          </button>
          <button 
            type="submit" 
            className="btn-primary"
            disabled={Object.keys(errors).length > 0}
          >
            {residente ? 'Guardar Cambios' : 'Guardar'}
          </button>
        </div>
      </form>
    </div>
  )
}

export default ResidenteForm
