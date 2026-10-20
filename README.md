# Agile Task Manager

Канбан-доска с рабочими пространствами, ролями, приглашениями и ИИ-ассистентом на локальной
модели.

**Стек:** FastAPI, SQLAlchemy, PostgreSQL, React, TypeScript, shadcn/ui, Ollama (`qwen2.5:3b`).

## Быстрый запуск (Docker)

Нужны Docker и [Ollama](https://ollama.com).

```bash
# 1. Локальная модель (на macOS ставится нативно — в Docker нет доступа к GPU)
brew install ollama && brew services start ollama
ollama pull qwen2.5:3b

# 2. Приложение
cp .env.example .env              # задайте JWT_SECRET
docker compose up --build
```

Откройте http://localhost:8080 и зарегистрируйтесь. Без Ollama приложение тоже работает,
только без ИИ-функций; `AI_ENABLED=false` в `.env` скрывает их полностью.

## Запуск для разработки

```bash
docker compose up -d db           # только PostgreSQL

cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload   # API: http://localhost:8000/docs

cd ../frontend
npm install && npm run dev        # http://localhost:5173
```

## ИИ-ассистент

- **Ассистент** — чат по задачам доски: сводка, просрочки, приоритеты, нагрузка.
- **Задачи с ИИ** — модель разбивает цель на задачи, вы выбираете, какие добавить.
- **Описание с ИИ** — черновик описания в карточке задачи.

## Тесты

```bash
docker compose up -d db
cd backend && uv run ruff check && uv run pytest
OLLAMA_LIVE=1 uv run pytest tests/test_ai_live.py   # с настоящей моделью
cd ../frontend && npm run build && npm run lint
```
