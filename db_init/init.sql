CREATE DATABASE redsoft_docker;

\c redsoft_docker;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL
);

CREATE TABLE containers (
    id VARCHAR(255) PRIMARY KEY,       
    name VARCHAR(255) NOT NULL,        
    image VARCHAR(255) NOT NULL        
);