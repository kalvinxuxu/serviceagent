# Runtime files

This directory contains local runtime artifacts and is intentionally excluded from version control.

- `logs/`: backend/frontend startup and runtime logs.
- `db/`: local database files and archived SQLite databases.
- `uploads/`: optional local upload staging area.

Docker Compose uses PostgreSQL for application state; the root `demo.db` is retained because the existing local `.env` points to it. New SQLite fallback runs use `runtime/db/shanye_demo.db`.
