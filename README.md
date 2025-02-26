# Muzzafar Courses Telegram Bot

A Telegram bot for managing Russian language courses, allowing students to access paid materials and enabling the teacher to manage courses and students.

## Installation
1. Install Poetry: `pip install poetry`
2. Clone the repository and navigate to the project directory.
3. Run `poetry install` to install dependencies.
4. Create a `.env` file with your bot token, database URL, admin ID, and private channel ID.
5. Set up a PostgreSQL database and update the `DATABASE_URL` in `.env`.
6. Run migrations: `alembic upgrade head`
7. Start the bot: `python -m muzzafar_courses`

## Usage
- **Students:** Use `/start` to begin, select courses, and access materials after payment.
- **Admin:** Use `/add_course` or `/add_student` to manage content and users.

## Tech Stack
- Python 3.12
- aiogram 3.18.0
- SQLAlchemy 2.0.38
- asyncpg 0.30.0
- Alembic 1.14.1