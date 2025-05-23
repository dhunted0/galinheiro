from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/covers'
ALLOWED_EXTENSIONS = {'jpg', 'png', 'webp'}


app = Flask(__name__)
DB = 'games.db'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                genre TEXT NOT NULL,
                platform TEXT NOT NULL,
                interprise TEXT NOT NULL,
                release_year INTEGER NOT NULL
            )
        ''')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# home page
@app.route('/')
def index():
    with sqlite3.connect(DB) as conn:
        games = conn.execute('SELECT * FROM games').fetchall()
    return render_template('index.html', games=games)

# add game page
@app.route('/add', methods=['GET', 'POST'])
def addGame():
    if request.method == 'POST':
        name = request.form['name']
        genre = request.form['genre']
        platform = request.form['platform']
        interprise = request.form['interprise']
        release_year = request.form['release_date']

        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()

            # verify if game already exists
            cursor.execute("SELECT id FROM games WHERE LOWER(name) = LOWER(?)", (name,))
            if cursor.fetchone():
                return render_template('addGame.html', error="A game with this name already exists.", form=request.form)

            # add new game to database
            cursor.execute('''
                INSERT INTO games (name, genre, platform, interprise, release_year)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, genre, platform, interprise, release_year))
            game_id = cursor.lastrowid

        # check if cover image is provided
        file = request.files.get('cover')
        if not file or file.filename == '':
            with sqlite3.connect(DB) as conn:
                conn.execute('DELETE FROM games WHERE id = ?', (game_id,))
            return render_template('addGame.html', error="Cover image is required.", form=request.form)

        # check if file is allowed
        if not allowed_file(file.filename):
            with sqlite3.connect(DB) as conn:
                conn.execute('DELETE FROM games WHERE id = ?', (game_id,))
            return render_template('addGame.html', error="Image must be JPG, PNG or WEBP.", form=request.form)

        # save the file
        filename = secure_filename(f"{game_id}.jpg")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        return redirect(url_for('index'))

    return render_template('addGame.html')

# edit game page
@app.route('/edit/<int:game_id>', methods=['GET', 'POST'])
def editGame(game_id):
    with sqlite3.connect(DB) as conn:
        game = conn.execute('SELECT * FROM games WHERE id = ?', (game_id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        genre = request.form['genre']
        platform = request.form['platform']
        interprise = request.form['interprise']
        release_year = request.form['release_date']

        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()

            # Verify if game already exists
            cursor.execute("SELECT id FROM games WHERE LOWER(name) = LOWER(?) AND id != ?", (name, game_id))
            if cursor.fetchone():
                return render_template('editGame.html', game=game, error="Another game with this name already exists.", form=request.form)

            # update game in database
            cursor.execute('''
                UPDATE games
                SET name = ?, genre = ?, platform = ?, interprise = ?, release_year = ?
                WHERE id = ?
            ''', (name, genre, platform, interprise, release_year, game_id))

        # upload new cover image if provided
        file = request.files.get('cover')
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"{game_id}.jpg")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        return redirect(url_for('index'))

    return render_template('editGame.html', game=game)


# delete game page
@app.route('/delete/<int:game_id>', methods=['POST'])
def deleteGame(game_id):
    with sqlite3.connect(DB) as conn:
        conn.execute('DELETE FROM games WHERE id = ?', (game_id,))
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
