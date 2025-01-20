Описание
Проект представляет собой API на базе FastAPI для управления пользователями и Docker-контейнерами, включая регистрацию, аутентификацию и основные операции с контейнерами, такие как запуск, остановка, удаление и клонирование из Git-репозитория.

Основные технологии
FastAPI - для построения веб-API
Docker - для управления контейнерами
PostgreSQL - база данных для хранения данных пользователей
Docker Compose - для контейнеризации базы данных PostgreSQL и запуска приложения
Poetry - для управления зависимостями

Требования
Для работы проекта необходимо установить следующие компоненты:

Python 3.11+
Docker и Docker Compose
Poetry для установки и управления зависимостями Python


Установка и запуск
1. Клонируйте репозиторий
git clone git@gitlab.red-soft.ru:group1/Borzenkov/redsoft.git
cd redsoft

2. Установите зависимости с помощью Poetry
poetry install

3. Запустите Docker Compose для базы данных
docker-compose up -d

4. Запустите приложение
poetry shell
uvicorn main:app --reload

5. Инициализация базы данных
CREATE DATABASE redsoft_docker;
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS containers (
    id VARCHAR(255) PRIMARY KEY,       
    name VARCHAR(255) NOT NULL,        
    image VARCHAR(255) NOT NULL        
);


Структура Git Flow
Проект использует стандартный Git Flow для управления ветками и релизами.

Основные ветки
main - Production-версия кода, содержащая стабильные релизы.
dev - Ветка для разработки, в которую вливаются изменения из всех веток с фичами и багфиксами.
Ветки для задач и фиксов
feat/[название_задачи] - Ветка для отдельной задачи, создаётся из dev, вливается обратно после завершения.
fix/[название_багфикса] - Ветка для исправления ошибок, создаётся из dev и вливается обратно.
hotfix/[дата] - Ветка для исправлений в production, создаётся из main, вливается в main и dev.
release/[версия] - Ветка релиза, создаётся из main, объединяется с dev и main.
Примеры именования веток
Фича: feat/authentication-form
Багфикс: fix/authentication-redirect
Подветка для одного разработчика: feat/authentication-form/AB
Коммиты
Коммиты именуются по формуле [тип задачи]: [описание], где тип задачи может быть следующим:

feat - добавление новой функциональности
fix - исправление ошибок
docs - изменения в документации
style - изменения в форматировании без изменения кода
refactor - рефакторинг кода
test - добавление тестов
chore - обновление конфигурационных файлов и служебного кода

Пример:
feat: добавлена форма авторизации пользователей
fix: исправлен редирект после авторизации
docs: добавлен раздел о настройке проекта


Документация API
Для доступа к документации API перейдите по адресу http://127.0.0.1:8000/docs после запуска приложения.