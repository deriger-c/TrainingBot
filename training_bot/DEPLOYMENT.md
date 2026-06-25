# Бесплатный деплой Training Bot

Цель: backend всегда доступен в облаке, Mini App открывается с телефона, AI-worker работает локально через Ollama, когда включён твой ПК.

## 1. Neon Postgres

1. Создай бесплатный проект в Neon.
2. Скопируй connection string.
3. Используй его как `DATABASE_URL` в backend host.

Обычный `postgres://...` можно вставлять как есть: backend сам приведёт его к async-драйверу.

## 2. Render backend

В корне git-репозитория лежит `render.yaml`. Render Blueprint по умолчанию ищет этот файл в корне репозитория, а внутри сервиса указан `rootDir: training_bot`.

1. Подключи GitHub-репозиторий к Render.
2. Создай Blueprint из `render.yaml`.
3. Заполни env vars:

```env
BOT_TOKEN=...
ADMIN_USER_ID=...
GOOGLE_SCRIPT_URL=...
GOOGLE_SCRIPT_SECRET=...
TELEGRAM_WEBHOOK_SECRET=...
DATABASE_URL=...
WORKER_TOKEN=...
PUBLIC_BASE_URL=https://your-render-service.onrender.com
MINIAPP_URL=https://your-miniapp.pages.dev
DEFAULT_TIMEZONE=Asia/Jerusalem
```

`PUBLIC_BASE_URL` должен быть публичным HTTPS URL backend. После первого деплоя Render покажет этот URL.

Проверка backend:

```powershell
curl https://your-render-service.onrender.com/health
```

Ожидаемый ответ:

```json
{"ok":true,"mode":"free-cloud"}
```

## 3. Cloudflare Pages Mini App

Проект Mini App лежит в `training_bot/miniapp`.

Cloudflare Pages settings:

```text
Root directory: training_bot/miniapp
Build command: npm run build
Build output directory: dist
Environment variable: VITE_API_BASE_URL=https://your-render-service.onrender.com
```

После деплоя скопируй Pages URL и добавь его в backend env var `MINIAPP_URL`, затем redeploy backend. Это нужно для CORS.

## 4. Telegram webhook

После деплоя backend запусти локально из папки `training_bot`:

```powershell
python -m scripts.set_webhook
```

Скрипт берёт:

```env
BOT_TOKEN=...
PUBLIC_BASE_URL=https://your-render-service.onrender.com
TELEGRAM_WEBHOOK_SECRET=...
```

Webhook будет установлен на:

```text
https://your-render-service.onrender.com/telegram/webhook
```

Если нужно вернуться к polling-режиму:

```powershell
python -m scripts.delete_webhook
python bot.py
```

## 5. Telegram Mini App button

В BotFather:

1. Открой своего бота.
2. Настрой Web App / Menu Button.
3. Укажи Cloudflare Pages URL.

После этого Mini App будет открываться прямо из Telegram.

## 6. Local AI-worker

На твоём ПК:

```powershell
ollama pull gemma3:4b
```

или другая локальная модель, которая у тебя установлена.

В `.env`:

```env
PUBLIC_BASE_URL=https://your-render-service.onrender.com
WORKER_TOKEN=...
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
```

Запуск:

```powershell
python -m local_ai.worker
```

Если worker выключен, backend и Mini App продолжают работать как обычный умный трекер.

## 7. Источники

- Render Blueprint ищется в `render.yaml` в корне репозитория по умолчанию: https://render.com/docs/blueprint-spec
- Cloudflare Pages для Vite использует `npm run build` и output `dist`: https://developers.cloudflare.com/pages/framework-guides/deploy-a-vite3-project/
- Telegram `setWebhook` принимает HTTPS URL для входящих update: https://core.telegram.org/bots/api#setwebhook
