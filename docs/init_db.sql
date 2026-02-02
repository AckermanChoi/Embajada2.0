-- =========================================================
-- SCRIPT INICIALIZADOR DE BASE DE DATOS PARA EL PROYECTO RESIDENTES
-- Autor: Monica Maria Briceño Gutierrez
-- Fecha: 2026-01-15
-- Descripción:
--   Este script elimina la base de datos si ya existe,
--   la vuelve a crear desde cero y define la tabla 'residentes' para la embajada.
-- =========================================================

-- 1️⃣ Borrar la base de datos si ya existe
DROP DATABASE IF EXISTS residentes_db;

-- 2️⃣ Crear una nueva base de datos
CREATE DATABASE residentes_db CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

-- 3️⃣ Seleccionar la base de datos recién creada
USE residentes_db;

-- 4️⃣ Crear tabla 'residentes' con los campos necesarios
CREATE TABLE residentes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    pasaporte VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(150) NOT NULL UNIQUE,
    telefono VARCHAR(50),
    direccion VARCHAR(255),
    ocupacion VARCHAR(100),
    estado_civil VARCHAR(20)
);

-- 5️⃣ Insertar algunos registros de ejemplo
INSERT INTO residentes (nombre, apellido, fecha_nacimiento, pasaporte, email, telefono, direccion, ocupacion, estado_civil) VALUES
('Juan', 'Pérez', '1985-03-15', 'A1234567', 'juan.perez@example.com', '555-0101', 'Calle 123, Ciudad', 'Ingeniero', 'Soltero'),
('María', 'García', '1990-07-22', 'B7654321', 'maria.garcia@example.com', '555-0102', 'Avenida 456, Ciudad', 'Doctora', 'Casada'),
('Carlos', 'Rodríguez', '1982-11-05', 'C9876543', 'carlos.rodriguez@example.com', '555-0103', 'Plaza 789, Ciudad', 'Abogado', 'Divorciado'),
('Ana', 'Martínez', '1995-02-28', 'D4567890', 'ana.martinez@example.com', '555-0104', 'Paseo 321, Ciudad', 'Arquitecta', 'Soltera'),
('Luis', 'López', '1988-09-12', 'E2345678', 'luis.lopez@example.com', '555-0105' , 	'Boulevard 654, Ciudad' , 	'Profesor' , 	'Casado');
-- 6️⃣ Confirmar la creación de la tabla y los registros
SELECT * FROM residentes;