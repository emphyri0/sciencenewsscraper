# Emphyrio.io — Science News Scraper

A simple yet elegant Flask-based web app that scrapes and displays English science news via RSS feeds. Built for Raspberry Pi 4 (running Pi OS Lite), designed with Tailwind and lucide icons, featuring dark mode, favorites, filtering, and responsive layout.

## ✨ Features

- 🔍 Full-text search
- 📡 Feed source filter
- ❤️ Save favorites
- 🌙 Dark mode toggle
- 🖼️ Grid & List views
- ♻️ Manual refresh
- 📰 Modal preview of articles
- 🔌 Designed to run 24/7 on Raspberry Pi

## 🚀 Getting Started

### Requirements

- Python 3.11+
- Flask
- feedparser
- python-dateutil

Install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run the app

```bash
python app.py
```

Access the web UI on:

```
http://<your-pi-ip>:5000
```

## 🛠️ Manage RSS Feeds

Click the 🟠 RSS icon in the header to manage sources.
You can:

- Add new feeds
- Toggle activation
- Delete feeds

## 📂 Project Layout

- `app.py`: Main Flask app
- `templates/index.html`: Front-end layout
- `news.db`: SQLite database
- `requirements.txt`: Dependencies
- `README.md`: This file

## 💡 Hosting

You can auto-start this app on boot via:

- systemd service
- Docker (optional)
- or just a cron job

## 👤 Author

[emphyrio.io](https://emphyrio.io)
