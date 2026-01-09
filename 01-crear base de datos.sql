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