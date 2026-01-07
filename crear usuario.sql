CREATE USER 'movesadmin'@'localhost' IDENTIFIED WITH mysql_native_password BY 'Movesadmin1234$';

GRANT ALL PRIVILEGES ON MovesLocation.* TO 'movesadmin'@'localhost';
FLUSH PRIVILEGES;
