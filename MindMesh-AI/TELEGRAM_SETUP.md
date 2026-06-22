<div align="center">
  <img src="assets/logo.png" width="180">
</div>

# MindMesh AI – Telegram Integration Setup Guide

This guide will walk you through enabling and configuring the full Telegram monitoring ecosystem for MindMesh AI.

## 1. Create a Bot via BotFather

1. Open Telegram and search for `@BotFather`.
2. Send the command `/newbot`.
3. Provide a name and a username (e.g., `MindMeshAdminBot`).
4. BotFather will provide an **HTTP API Token**. Save this.

## 2. Retrieve Your Admin Chat ID

1. Search for `@userinfobot` or `@RawDataBot` in Telegram.
2. Send any message or `/start`.
3. It will return your unique `id` (e.g., `123456789`). This is your Admin Chat ID.

## 3. Configure Environment Variables

Update your `.env` file with these values:

```env
TELEGRAM_BOT_TOKEN=your_http_api_token
TELEGRAM_ADMIN_CHAT_ID=your_chat_id

# Set to true to enable alerts and bot
TELEGRAM_ENABLED=true

# If using Webhooks in production, enter your public domain URL
TELEGRAM_WEBHOOK_URL=https://mindmesh.example.com/api/telegram/webhook

# Scheduled Task Intervals
MONITOR_INTERVAL_MINUTES=5
DAILY_REPORT_HOUR=9
```

## 4. Polling vs Webhooks

**Local Development (Polling)**:
If you leave `TELEGRAM_WEBHOOK_URL` empty in your `.env`, the FastAPI application will automatically start a long-polling background task when you run `uvicorn main:app`. This allows you to test commands locally without a public IP.

**Production (Webhooks)**:
If `TELEGRAM_WEBHOOK_URL` is set, long-polling is disabled. You must tell Telegram where to send updates by registering the webhook:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -d "url=https://mindmesh.example.com/api/telegram/webhook"
```

## 5. Features & Commands

Once running, send these commands to your bot:

* `/status` - Core system and environment status.
* `/uptime` - Application uptime since the process started.
* `/stats` - Daily statistics (users, queries, uploads).
* `/health` - HTTP health check of your core routes.
* `/qdrant` - Check Qdrant Cloud connectivity.
* `/gemini` / `/groq` - Check LLM provider availability.
* **AI Chat**: Simply type a regular question (e.g. "What is flexbox?") and the bot will perform a RAG search and answer you using the configured LLM.

## 6. Automated Monitoring

The system automatically performs:
* **Security Checks**: Monitors IP rate limits and issues alerts for 50+ requests per minute.
* **Health Polling**: Pings all frontend routes every 5 minutes and alerts on timeout > 5s or HTTP 500s.
* **Resource Monitoring**: Sends alerts if CPU or RAM usage exceeds 85%.
* **GitHub Actions**: Sends build and deployment success/failure messages directly to your chat ID.
