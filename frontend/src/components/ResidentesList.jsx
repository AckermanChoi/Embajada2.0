function ResidentesList({ residentes, onEdit, onDelete, page, totalPages, onPageChange }) {
  if (residentes.length === 0) {
    return (
      <div className="table-container">
        <div className="empty-state">
          <h2>Sin residentes registrados</h2>
          <p>Haz clic en "Agregar Residente" para comenzar</p>
        </div>
      </div>
    )
  }

  return (
    <div className="table-container">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Nombre</th>
            <th>Apellido</th>
            <th>Email</th>
            <th>Teléfono</th>
            <th>Ocupación</th>
            <th>Estado Civil</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {residentes.map(residente => (
            <tr key={residente.id}>
              <td>{residente.id}</td>
              <td>{residente.nombre}</td>
              <td>{residente.apellido}</td>
              <td>{residente.email}</td>
              <td>{residente.telefono || '-'}</td>
              <td>{residente.ocupacion || '-'}</td>
              <td>{residente.estado_civil || '-'}</td>
              <td>
                <div className="actions">
                  <button
                    className="btn-secondary"
                    onClick={() => onEdit(residente.id)}
                  >
                    Editar
                  </button>
                  <button
                    className="btn-danger"
                    onClick={() => onDelete(residente.id)}
                  >
                    Eliminar
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {totalPages > 1 && (
        <div className="pagination">
          <button
            className="page-btn"
            onClick={() => onPageChange(page - 1)}
            disabled={page === 1}
          >
            Anterior
          </button>
          <div className="page-numbers">
            {Array.from({ length: totalPages }, (_, index) => {
              const pageNumber = index + 1
              return (
                <button
                  key={pageNumber}
                  className={`page-btn ${pageNumber === page ? 'active' : ''}`}
                  onClick={() => onPageChange(pageNumber)}
                >
                  {pageNumber}
                </button>
              )
            })}
          </div>
          <button
            className="page-btn"
            onClick={() => onPageChange(page + 1)}
            disabled={page === totalPages}
          >
            Siguiente
          </button>
        </div>
      )}
    </div>
  )
}

export default ResidentesList
