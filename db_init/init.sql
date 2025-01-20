CREATE DATABASE redsoft_docker;

\c redsoft_docker;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL
);