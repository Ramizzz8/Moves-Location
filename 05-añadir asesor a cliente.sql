ALTER TABLE user
ADD COLUMN advisor_id INT NULL,
ADD CONSTRAINT fk_user_advisor
FOREIGN KEY (advisor_id) REFERENCES user(id);
