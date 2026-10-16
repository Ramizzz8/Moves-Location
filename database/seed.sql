-- ============================================================
-- Moves Location · Datos de demostración (todos ficticios)
-- Contraseña de todas las cuentas: Demo1234!
--   admin@moves.demo    → panel de administración
--   cliente@moves.demo  → área de cliente con proceso, documentos y mensajes
-- ============================================================

SET NAMES utf8mb4;

INSERT INTO document_types (id, name) VALUES
(1, 'Pasaporte'),
(2, 'Formulario de solicitud'),
(3, 'Certificado de antecedentes penales'),
(4, 'Comprobante de domicilio'),
(5, 'Contrato de trabajo'),
(6, 'Seguro médico');

SET @pw = 'scrypt:32768:8:1$NcOIyVLnfg5sx5v4$07fd5df85063f9153da49914441a22c7890c44c2c2a90e0b30e457cef87c37b8a7057f739ced3a06870810db8de052e8dd45b13ae85503b1934e803a5b8ed652';

INSERT INTO user (id, first_name, last_name, email, phone, country, password, role, advisor_id) VALUES
(1,  'Admin',   'Moves',     'admin@moves.demo',          '+34 600 000 001', 'ES', @pw, 'admin',   NULL),
(2,  'Carmen',  'Ortega',    'carmen.ortega@moves.demo',  '+34 600 000 002', 'ES', @pw, 'advisor', NULL),
(3,  'Javier',  'Navarro',   'javier.navarro@moves.demo', '+34 600 000 003', 'ES', @pw, 'advisor', NULL),
(4,  'Laura',   'Gómez',     'cliente@moves.demo',        '+57 300 000 0004', 'CO', @pw, 'client', 2),
(5,  'Mateo',   'Fernández', 'mateo.f@ejemplo.com',       '+54 11 0000 0005', 'AR', @pw, 'client', 2),
(6,  'Valentina','Rojas',    'valentina.r@ejemplo.com',   '+56 9 0000 0006',  'CL', @pw, 'client', 3),
(7,  'Diego',   'Castillo',  'diego.c@ejemplo.com',       '+52 55 0000 0007', 'MX', @pw, 'client', 3),
(8,  'Sofía',   'Herrera',   'sofia.h@ejemplo.com',       '+51 900 000 008',  'PE', @pw, 'client', NULL),
(9,  'Andrés',  'Molina',    'andres.m@ejemplo.com',      '+58 412 000 0009', 'VE', @pw, 'client', NULL);

INSERT INTO processes (user_id, advisor_id, advisor_name, destination_country, visa_type, start_date, status, updated_at) VALUES
(4, 2, 'Carmen Ortega',  'España',   'Visado de búsqueda de empleo', DATE_SUB(CURDATE(), INTERVAL 40 DAY), 'in_review', DATE_SUB(NOW(), INTERVAL 2 DAY)),
(5, 2, 'Carmen Ortega',  'Portugal', 'Visado de nómada digital',     DATE_SUB(CURDATE(), INTERVAL 25 DAY), 'pending',   DATE_SUB(NOW(), INTERVAL 5 DAY)),
(6, 3, 'Javier Navarro', 'Canadá',   'Permiso de estudios',          DATE_SUB(CURDATE(), INTERVAL 90 DAY), 'completed', DATE_SUB(NOW(), INTERVAL 10 DAY)),
(7, 3, 'Javier Navarro', 'España',   'Arraigo para la formación',    DATE_SUB(CURDATE(), INTERVAL 12 DAY), 'pending',   DATE_SUB(NOW(), INTERVAL 1 DAY)),
(8, NULL, NULL,          'Alemania', 'Tarjeta azul UE',              DATE_SUB(CURDATE(), INTERVAL 3 DAY),  'pending',   DATE_SUB(NOW(), INTERVAL 3 HOUR));

-- Los archivos de ejemplo están en database/demo-uploads/ y se copian a uploads/ al reiniciar
INSERT INTO documents (user_id, type_id, file_path, status, uploaded_at) VALUES
(4, 1, 'demo_pasaporte.pdf',     'approved', DATE_SUB(NOW(), INTERVAL 35 DAY)),
(4, 2, 'demo_solicitud.pdf',     'approved', DATE_SUB(NOW(), INTERVAL 30 DAY)),
(4, 3, 'demo_antecedentes.pdf',  'pending',  DATE_SUB(NOW(), INTERVAL 4 DAY)),
(5, 1, 'demo_pasaporte.pdf',     'pending',  DATE_SUB(NOW(), INTERVAL 6 DAY)),
(6, 1, 'demo_pasaporte.pdf',     'approved', DATE_SUB(NOW(), INTERVAL 80 DAY)),
(6, 6, 'demo_seguro.pdf',        'approved', DATE_SUB(NOW(), INTERVAL 70 DAY)),
(7, 4, 'demo_domicilio.pdf',     'rejected', DATE_SUB(NOW(), INTERVAL 2 DAY));

INSERT INTO messages (sender_id, receiver_id, content, created_at, is_read) VALUES
(2, 4, 'Hola Laura, soy Carmen, tu asesora. Ya he revisado tu pasaporte y el formulario: todo correcto.', DATE_SUB(NOW(), INTERVAL 29 DAY), TRUE),
(4, 2, '¡Gracias Carmen! ¿Qué me falta para completar el expediente?', DATE_SUB(NOW(), INTERVAL 28 DAY), TRUE),
(2, 4, 'Solo el certificado de antecedentes penales apostillado. Cuando lo tengas, súbelo desde la pestaña de documentos.', DATE_SUB(NOW(), INTERVAL 27 DAY), TRUE),
(4, 2, 'Listo, lo acabo de subir. ¿Cuánto suele tardar la revisión?', DATE_SUB(NOW(), INTERVAL 4 DAY), TRUE),
(2, 4, 'Entre 3 y 5 días hábiles. Te aviso por aquí en cuanto esté validado.', DATE_SUB(NOW(), INTERVAL 3 DAY), FALSE);
