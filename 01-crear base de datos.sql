-- Archivo: moveslocation.sql
-- Base de datos para el sistema de servicios migratorios de la empresa MovesLocation


-- Crear base de datos
CREATE DATABASE IF NOT EXISTS MovesLocation;
USE MovesLocation;


-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS users (
id INT AUTO_INCREMENT PRIMARY KEY,
email VARCHAR(120) NOT NULL UNIQUE,
password VARCHAR(200) NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Tabla de documentos
CREATE TABLE IF NOT EXISTS documents (
id INT AUTO_INCREMENT PRIMARY KEY,
filename VARCHAR(200) NOT NULL,
user_id INT NOT NULL,
uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


-- Tabla de procesos migratorios
CREATE TABLE IF NOT EXISTS processes (
id INT AUTO_INCREMENT PRIMARY KEY,
user_id INT NOT NULL,
status VARCHAR(50) DEFAULT 'En revisión',
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


-- Tabla de planes de apoyo
CREATE TABLE IF NOT EXISTS plans (
id INT AUTO_INCREMENT PRIMARY KEY,
name VARCHAR(50) NOT NULL,
description TEXT,
price DECIMAL(10,2) DEFAULT 0.00
);


-- Tabla de reseñas
CREATE TABLE IF NOT EXISTS reviews (
id INT AUTO_INCREMENT PRIMARY KEY,
user_id INT NOT NULL,
rating INT NOT NULL CHECK(rating >=1 AND rating <=5),
comment TEXT,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,               -- Usuario que recibe/el mensaje está relacionado con este ID
    sender_name VARCHAR(100) NOT NULL,  -- Nombre de quien envía el mensaje (ej: asesor o admin)
    message TEXT NOT NULL,              -- Contenido del mensaje
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Fecha de envío
    read_status BOOLEAN DEFAULT FALSE,  -- Indica si el usuario ya leyó el mensaje
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- Tabla de tipos de documentos
CREATE TABLE document_types (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL
);

-- Insert de ejemplo de tipos de documentos
INSERT INTO document_types (name) VALUES
('Pasaporte'),
('Formulario de Solicitud'),
('Certificado de Antecedentes'),
('Comprobante de Domicilio');

CREATE TABLE messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,               
    sender_name VARCHAR(100) NOT NULL,  
    message TEXT NOT NULL,              
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_status BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


ALTER TABLE documents
ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending' AFTER type_id,
ADD COLUMN uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP AFTER status,
ADD CONSTRAINT fk_type
FOREIGN KEY (type_id) REFERENCES document_types(id);