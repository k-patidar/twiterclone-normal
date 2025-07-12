from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB_NAME = "twitter_clone.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS tweets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

@app.route("/")
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT tweets.content, tweets.created_at, users.username
            FROM tweets
            JOIN users ON tweets.user_id = users.id
            ORDER BY tweets.created_at DESC
        ''')
        tweets = c.fetchall()
    return render_template("index.html", tweets=tweets, username=session['username'])

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                return "Username already taken."
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
            user = c.fetchone()
            if user:
                session['username'] = username
                session['user_id'] = user[0]
                return redirect(url_for('index'))
            else:
                return "Invalid credentials."
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/tweet", methods=["POST"])
def tweet():
    if 'username' not in session:
        return redirect(url_for('login'))
    content = request.form["content"]
    user_id = session['user_id']
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO tweets (user_id, content) VALUES (?, ?)", (user_id, content))
        conn.commit()
    return redirect(url_for('index'))

@app.route("/profile")
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT content, created_at FROM tweets
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (session['user_id'],))
        tweets = c.fetchall()
    return render_template("profile.html", tweets=tweets, username=session['username'])

if __name__ == "__main__":
    if not os.path.exists(DB_NAME):
        init_db()
    app.run(debug=True)
