# Training Bot

Telegram-бот на Python 3.12+ и aiogram 3.x для пошагового ведения тренировок Workout A / Workout B: разминка, упражнения, отдых, ввод результатов, итог, Google Sheets и локальный backup.

## 1. Создать Telegram-бота через BotFather

1. Открой Telegram.
2. Найди `@BotFather`.
3. Напиши `/newbot`.
4. Введи название бота.
5. Введи username, который заканчивается на `bot`.

## 2. Получить BOT_TOKEN

BotFather выдаст токен вида:

```text
1234567890:AA....
```

Сохрани его для файла `.env`.

## 3. Создать Google Sheet

1. Открой [Google Sheets](https://sheets.google.com).
2. Создай новую таблицу.
3. Назови её, например, `Training Bot`.

## 4. Какие листы создать

Можно не создавать вручную: `Code.gs` создаст листы сам при первом запросе.

Листы:

```text
Workout Sessions
Exercise Results
Goals
Exercise Library
Progress
Settings
```

## 5. Вставить Apps Script

1. В Google Sheet открой `Extensions` -> `Apps Script`.
2. Удали старый код.
3. Вставь содержимое файла `apps_script/Code.gs`.
4. Нажми `Save`.

## 6. Задеплоить Apps Script как Web App

1. Нажми `Deploy` -> `New deployment`.
2. Тип выбери `Web app`.
3. `Execute as`: `Me`.
4. `Who has access`: `Anyone`.
5. Нажми `Deploy`.
6. Дай разрешения Google-аккаунту.

## 7. Получить WEB_APP_URL

После деплоя Google покажет `Web app URL`. Скопируй его в `.env` как `GOOGLE_SCRIPT_URL`.

Для проверки открой в браузере:

```text
WEB_APP_URL?action=setup&secret=long_random_secret
```

Ответ должен быть JSON с `ok: true`.

## 8. Заполнить .env

Скопируй `.env.example` в `.env`:

```powershell
copy .env.example .env
```

Заполни:

```env
BOT_TOKEN=your_telegram_bot_token
GOOGLE_SCRIPT_URL=your_google_apps_script_web_app_url
GOOGLE_SCRIPT_SECRET=long_random_secret
ADMIN_USER_ID=your_telegram_user_id
DEFAULT_TIMEZONE=Asia/Jerusalem
```

`ADMIN_USER_ID` ограничивает доступ к боту одним Telegram-пользователем. Если оставить поле пустым или `your_telegram_user_id`, бот будет доступен всем, кто знает username бота.

`GOOGLE_SCRIPT_SECRET` должен совпадать с Apps Script property `BOT_SECRET`. Это защищает публичный Web App URL от посторонних запросов.

Чтобы задать секрет в Apps Script:

1. Открой `Project Settings`.
2. В блоке `Script Properties` добавь property:

```text
BOT_SECRET=тот_же_long_random_secret
```

3. Нажми `Save`.

## 9. Установить зависимости

Открой PowerShell в папке `training_bot`:

```powershell
cd "C:\Users\USER\Documents\training plan\training_bot"
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Если PowerShell блокирует активацию venv:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 10. Запустить бота на Windows

```powershell
cd "C:\Users\USER\Documents\training plan\training_bot"
.\.venv\Scripts\Activate.ps1
python bot.py
```

В Telegram нажми `/start`.

## 11. Проверить, что сохранение работает

1. Запусти `/start`.
2. Выбери `🔥 Быстрый ввод результата`.
3. Введи:

```text
Подтягивания +5kg 6/5/5/4
```

4. Выбери тренировку `A`.
5. Открой лист `Exercise Results`.
6. Должна появиться новая строка.

Для проверки полной тренировки начни `/workout_a`, пройди несколько упражнений и нажми `Завершить тренировку` -> `Сохранить`.

## 12. Типичные ошибки

`Не задан BOT_TOKEN в .env`

Проверь, что файл называется именно `.env`, лежит рядом с `bot.py`, и токен не оставлен как `your_telegram_bot_token`.

`Google Script вернул не JSON`

Обычно это значит, что вставлен не Web App URL, деплой не опубликован или доступ не выставлен как `Anyone`.

`Unauthorized`

Проверь, что `GOOGLE_SCRIPT_SECRET` в `.env` совпадает с property `BOT_SECRET` в Apps Script.

`Нет доступа к этому боту`

Если задан `ADMIN_USER_ID`, бот отвечает только этому Telegram ID. Проверь свой ID и значение в `.env`.

`Не удалось сохранить в Google Sheets`

Бот не падает: данные сохраняются локально в `data/pending_workouts.json`. После исправления Google Script запусти:

```text
/sync
```

`ModuleNotFoundError`

Активируй виртуальное окружение и поставь зависимости:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`Forbidden: bot was blocked by the user`

Пользователь заблокировал бота. Разблокируй его в Telegram и снова нажми `/start`.

## Структура проекта

```text
training_bot/
  bot.py
  config.py
  requirements.txt
  .env.example
  README.md
  data/
    exercise_program.py
    local_backup.json
    pending_workouts.json
  handlers/
    start.py
    workout.py
    history.py
    progress.py
    goals.py
    settings.py
    quick_add.py
    common.py
  keyboards/
    main_menu.py
    workout_keyboards.py
    goals_keyboards.py
    settings_keyboards.py
  models/
    exercise.py
    workout.py
    goal.py
    settings.py
  services/
    google_sheets_api.py
    workout_service.py
    progress_service.py
    timer_service.py
  states/
    workout_states.py
    goal_states.py
    settings_states.py
    quick_add_states.py
  utils/
    logger.py
    formatters.py
    validators.py
    time_utils.py
  apps_script/
    Code.gs
```

## Как добавить Workout C

1. Открой `data/exercise_program.py`.
2. Добавь новый ключ `"C"` в словарь `WORKOUTS`.
3. Добавь команду/кнопку по аналогии с Workout A/B в `keyboards/main_menu.py` и `handlers/workout.py`.

Упражнения, планы, отдых, подсказки и примеры ввода живут только в `data/exercise_program.py`.

## Импорт первой тренировки

В проект добавлены данные первой тренировки от `16.06.2026 17:30–19:00`.

После настройки `GOOGLE_SCRIPT_URL` запусти в Telegram:

```text
/import_first_workout
```

Бот сохранит сессию, результаты упражнений и базовый прогресс. Если Google Sheets недоступен, импорт попадёт в `data/pending_workouts.json`. После исправления доступа запусти:

```text
/sync
```

## RIR, боль и прогрессия

После каждого результата бот теперь спрашивает:

```text
Сколько чистых повторений оставалось в запасе?
Была ли боль?
Техника была чистой?
Для стойки: были ли падения?
```

RIR проще RPE:

```text
RIR 4+ ≈ RPE 6
RIR 3  ≈ RPE 7
RIR 2  ≈ RPE 8
RIR 1  ≈ RPE 9
RIR 0  ≈ RPE 10
```

Бот не предлагает повышать вес, если была боль, техника не подтверждена, подход был тестом максимума, результат несопоставим или это только первая успешная тренировка на уровне.

## Бесплатная cloud + Mini App архитектура

Проект теперь можно запускать двумя способами:

```powershell
python bot.py
```

Polling-режим старого Telegram-бота.

```powershell
uvicorn web_app:app --host 0.0.0.0 --port 8000
```

FastAPI backend для Telegram webhook, Mini App и локального AI-worker.

Новые переменные `.env`:

```env
DATABASE_URL=sqlite+aiosqlite:///./data/training_bot.db
WORKER_TOKEN=change_me_to_a_long_random_worker_token
TELEGRAM_WEBHOOK_SECRET=change_me_to_a_long_random_telegram_webhook_secret
PUBLIC_BASE_URL=https://your-free-backend.example.com
MINIAPP_URL=https://your-cloudflare-pages-site.pages.dev
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

Для Neon Postgres используй `DATABASE_URL` из Neon. Обычный `postgres://...` бот сам нормализует в `postgresql+asyncpg://...`.

### Backend endpoints

```text
GET  /health
POST /telegram/webhook
GET  /api/miniapp/dashboard
POST /api/miniapp/workouts
POST /api/miniapp/workouts/{workout_id}/sets
POST /api/miniapp/workouts/{workout_id}/finish
GET  /api/coach/pending
POST /api/coach/recommendations
```

Mini App endpoints требуют Telegram header `X-Telegram-Init-Data`. Coach endpoints требуют `X-Worker-Token`.

Для полного бесплатного деплоя смотри [DEPLOYMENT.md](DEPLOYMENT.md).

### Локальный AI-worker

1. Установи Ollama.
2. Загрузи модель:

```powershell
ollama pull llama3.1:8b
```

3. Укажи `PUBLIC_BASE_URL` и `WORKER_TOKEN` в `.env`.
4. Запусти:

```powershell
python -m local_ai.worker
```

Worker прочитает завершённые тренировки, попросит локальный Ollama сделать разбор и сохранит рекомендацию в backend. Если Ollama выключен, бот продолжит работать без AI.

Чтобы worker работал как регулярный помощник, запусти loop-режим:

```powershell
python -m local_ai.worker --loop
```

По умолчанию он проверяет новые тренировки раз в 15 минут. Интервал можно поменять:

```powershell
python -m local_ai.worker --loop --interval 300
```

`300` означает 300 секунд, то есть 5 минут. Минимальный интервал внутри worker ограничен 60 секундами, чтобы случайно не забивать бесплатный backend частыми запросами.

В Mini App на вкладке коуча показывается статус локального AI:

```text
Локальный AI свежий
N тренировок ждут локальный AI
AI-разбор появится после запуска worker
```

Важно: если компьютер выключен или Ollama не запущен, Telegram-бот и Mini App всё равно продолжают работать. Просто AI-разборы появятся позже, когда worker снова стартует.

### Mini App

Код Mini App лежит в `miniapp/`.

```powershell
cd miniapp
npm install
npm run build
```

Для Cloudflare Pages:

```text
Build command: npm run build
Build output directory: dist
Environment variable: VITE_API_BASE_URL=https://your-free-backend.example.com
```

После деплоя добавь URL в `MINIAPP_URL` и настрой кнопку Web App через BotFather.
