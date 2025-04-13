from flask import Flask, render_template, redirect, url_for, request
import sqlite3
import feedparser
import math

app = Flask(__name__)


DB_PATH = 'news.db'

# --- DATABASE SETUP ---
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                summary TEXT,
                url TEXT,
                date TEXT,
                favorite INTEGER DEFAULT 0,
                feed_id INTEGER
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS feeds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                name TEXT,
                active INTEGER DEFAULT 1
            )
        ''')
        try:
            c.execute("ALTER TABLE news ADD COLUMN favorite INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            c.execute("ALTER TABLE feeds ADD COLUMN name TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            c.execute("ALTER TABLE feeds ADD COLUMN active INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            pass
        try:
            c.execute("ALTER TABLE news ADD COLUMN feed_id INTEGER")
        except sqlite3.OperationalError:
            pass
        conn.commit()

# --- SCRAPER FUNCTION ---
def scrape_news():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, url FROM feeds WHERE active = 1")
        feeds = c.fetchall()

        if not feeds:
            default_feed = "https://www.sciencedaily.com/rss/top/science.xml"
            c.execute("INSERT OR IGNORE INTO feeds (url, name, active) VALUES (?, ?, 1)", (default_feed, "ScienceDaily"))
            conn.commit()
            c.execute("SELECT id, url FROM feeds WHERE url = ?", (default_feed,))
            feeds = c.fetchall()

        for feed_id, feed_url in feeds:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries:
                title = entry.title
                summary = entry.summary
                link = entry.link
                date = entry.published

                c.execute("SELECT favorite FROM news WHERE url = ?", (link,))
                row = c.fetchone()

                if row:
                    favorite = row[0]
                    c.execute("""
                        UPDATE news 
                        SET title = ?, summary = ?, date = ?, favorite = ?, feed_id = ? 
                        WHERE url = ?
                    """, (title, summary, date, favorite, feed_id, link))
                else:
                    c.execute("""
                        INSERT INTO news (title, summary, url, date, favorite, feed_id)
                        VALUES (?, ?, ?, ?, 0, ?)
                    """, (title, summary, link, date, feed_id))

        conn.commit()

# --- MAIN PAGE + SEARCH + PAGINATION ---
@app.route('/')
def index():
    query = request.args.get("q", "")
    page = int(request.args.get("page", 1))
    per_page = 30
    offset = (page - 1) * per_page
    favorites_only = request.args.get("favorites") == "1"
    selected_feed = request.args.get("feed")

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, name FROM feeds WHERE active = 1")
        all_feeds = c.fetchall()

        filters = []
        params = []

        if favorites_only:
            filters.append("news.favorite = 1")

        if selected_feed:
            filters.append("feeds.id = ?")
            params.append(selected_feed)

        if query:
            filters.append("(news.title LIKE ? OR news.summary LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])

        where_clause = " AND ".join(filters)
        if where_clause:
            where_clause = "WHERE " + where_clause

        base_query = f"FROM news LEFT JOIN feeds ON news.feed_id = feeds.id {where_clause}"
        count_query = f"SELECT COUNT(*) {base_query}"
        data_query = f"SELECT news.id, news.title, news.summary, news.url, news.date, news.favorite, feeds.name {base_query} ORDER BY news.date DESC LIMIT ? OFFSET ?"

        c.execute(count_query, params)
        total = c.fetchone()[0]
        c.execute(data_query, (*params, per_page, offset))
        articles = c.fetchall()
        total_pages = max(1, math.ceil(total / per_page))

    return render_template(
        'index.html',
        articles=articles,
        page=page,
        total_pages=total_pages,
        query=query,
        favorites_only=favorites_only,
        selected_feed=selected_feed,
        all_feeds=all_feeds
    )

# --- FAVORITE TOGGLE ---
@app.route('/favorite/<int:article_id>')
def toggle_favorite(article_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT favorite FROM news WHERE id = ?", (article_id,))
        row = c.fetchone()
        if row:
            new_value = 0 if row[0] == 1 else 1
            c.execute("UPDATE news SET favorite = ? WHERE id = ?", (new_value, article_id))
            conn.commit()
    return redirect(request.referrer or url_for('index'))

# --- ADD FEED ---
@app.route('/feeds', methods=['GET', 'POST'])
def manage_feeds():
    message = ""
    if request.method == 'POST':
        feed_url = request.form.get('feed_url')
        feed_name = request.form.get('feed_name') or "Onbekend"
        if feed_url:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO feeds (url, name) VALUES (?, ?)", (feed_url, feed_name))
                    conn.commit()
                    message = "Feed toegevoegd."
                except sqlite3.IntegrityError:
                    message = "Feed bestaat al."

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, url, name, active FROM feeds")
        feeds = c.fetchall()

    return render_template('feeds.html', feeds=feeds, message=message)

# --- DELETE FEED ---
@app.route('/feeds/delete/<int:feed_id>', methods=['POST'])
def delete_feed(feed_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM feeds WHERE id = ?", (feed_id,))
        conn.commit()
    return redirect(url_for('manage_feeds'))

# --- TOGGLE FEED ACTIVE ---
@app.route('/feeds/toggle/<int:feed_id>', methods=['POST'])
def toggle_feed(feed_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT active FROM feeds WHERE id = ?", (feed_id,))
        row = c.fetchone()
        if row:
            new_status = 0 if row[0] == 1 else 1
            c.execute("UPDATE feeds SET active = ? WHERE id = ?", (new_status, feed_id))
            conn.commit()
    return redirect(url_for('manage_feeds'))

# --- MANUELE REFRESH ---
@app.route('/refresh')
def refresh():
    scrape_news()
    return redirect(url_for('index'))

# --- START APP ---
if __name__ == '__main__':
    init_db()
    scrape_news()
    app.run(host='0.0.0.0', port=5000, debug=True)
