-- ============================================================
-- Moves Location · Esquema de la base de datos (MySQL 8 / MariaDB)
-- Coincide con los modelos y consultas de app.py.
-- ============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS messages, documents, processes, document_types, user;

-- Usuarios: clientes, asesores y administradores
CREATE TABLE user (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    first_name  VARCHAR(100) NOT NULL,
    last_name   VARCHAR(100) NOT NULL,
    email       VARCHAR(120) NOT NULL UNIQUE,
    phone       VARCHAR(20),
    country     VARCHAR(50),
    password    VARCHAR(200) NOT NULL,
    role        VARCHAR(20) DEFAULT 'client',
    advisor_id  INT NULL,
    CONSTRAINT fk_user_advisor FOREIGN KEY (advisor_id) REFERENCES user(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tipos de documento que el cliente puede subir
CREATE TABLE document_types (
    id   INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Procesos migratorios de cada cliente
CREATE TABLE processes (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    user_id             INT NOT NULL,
    advisor_id          INT NULL,
    advisor_name        VARCHAR(200),
    destination_country VARCHAR(80),
    visa_type           VARCHAR(100),
    start_date          DATE,
    status              VARCHAR(50) DEFAULT 'pending',
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)    REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (advisor_id) REFERENCES user(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Documentos subidos por los clientes
CREATE TABLE documents (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    type_id     INT NOT NULL,
    file_path   VARCHAR(255) NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'pending',
    uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (type_id) REFERENCES document_types(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Mensajes entre cliente y asesor
CREATE TABLE messages (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    sender_id   INT NOT NULL,
    receiver_id INT NOT NULL,
    content     TEXT NOT NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_read     BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (sender_id)   REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES user(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
