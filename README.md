# Agile Task Manager

Канбан-доска с рабочими пространствами, ролями и приглашениями.
Контракт между бэкендом и фронтендом описан в [SPEC.md](SPEC.md).

## Стек

- **Бэкенд**: Python 3.12, FastAPI, SQLAlchemy 2 (async, asyncpg), Alembic, pydantic-settings,
  PyJWT, pwdlib (argon2). Менеджер пакетов — **uv**. Линтер/форматтер — ruff.
- **БД**: PostgreSQL 16 (docker compose).
- **Фронтенд**: Vite, React 19, TypeScript, Tailwind CSS v4, shadcn/ui, TanStack Query, dnd-kit.
- **Инфраструктура**: docker compose (`db`, `backend`, `frontend` — nginx раздаёт сборку и проксирует `/api`).

## Структура

```
backend/
  pyproject.toml, uv.lock, alembic.ini, Dockerfile
  alembic/versions/0001_initial.py   # единственная миграция, проверена вручную
  src/app/
    main.py                          # create_app(): роутеры, CORS, обработчики ошибок
    models.py                        # импорт всех моделей (для Alembic и мапперов)
    core/                            # config, db, security, errors, deps
    modules/{auth,users,workspaces,boards,tasks}/
                                     # models -> repository -> service -> router (+ schemas)
  tests/                             # pytest против настоящего Postgres
frontend/                            # Vite + React
docker-compose.yml, .env.example
```

Слои модуля: `repository` — только запросы, `service` — бизнес-правила и проверки прав
(бросает доменные ошибки `NotFound`/`Forbidden`/`Conflict`/`Unauthorized`/`ValidationError`),
`router` — тонкий слой. Одна функция `require_role` (`modules/workspaces/service.py`) отвечает за
все проверки ролей: не участник — 404, недостаточная роль — 403. Все ошибки возвращаются как
`{"detail": "...", "code": "..."}`.

## Локальный запуск бэкенда (uv + docker для БД)

Нужны [uv](https://docs.astral.sh/uv/) и Docker.

```bash
cp .env.example .env              # один раз
docker compose up -d db           # только PostgreSQL
cd backend
uv sync                           # установить зависимости
uv run alembic upgrade head       # применить миграции
uv run uvicorn app.main:app --reload
```

API: http://localhost:8000/api, документация: http://localhost:8000/docs.
Переменные читаются из окружения или `backend/.env` (см. `.env.example`).

Фронтенд:

```bash
cd frontend && npm install && npm run dev
```

## Тесты

Тесты идут в настоящий Postgres. Поднимите `db`, остальное сделает фикстура: она создаёт
отдельную базу `<имя>_test` (пересоздаётся при каждом запуске), накатывает миграции Alembic и
оборачивает каждый тест в транзакцию, которая откатывается в конце.

```bash
docker compose up -d db
cd backend
uv run ruff check && uv run ruff format --check && uv run pytest
```

## Запуск всего стека

```bash
cp .env.example .env              # обязательно задайте JWT_SECRET
docker compose up --build
```

Приложение: http://localhost:8080. Бэкенд при старте сам выполняет `alembic upgrade head`.
Данные БД хранятся в volume `pgdata`; `docker compose down -v` удалит их.

## Миграции

Схема меняется только через Alembic (`create_all` в приложении не используется).

```bash
cd backend
uv run alembic revision --autogenerate -m "add something"   # сгенерировать черновик
# обязательно просмотрите и поправьте файл в alembic/versions/ вручную
uv run alembic upgrade head                                 # применить
uv run alembic downgrade -1                                 # откатить последнюю
uv run alembic check                                        # модели совпадают со схемой?
```

После изменения моделей запустите `alembic check` — он не должен находить различий.
