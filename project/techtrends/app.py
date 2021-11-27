import sqlite3
import logging
import sys
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort


OPENED_CONNECTIONS = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    global OPENED_CONNECTIONS, ACTIVE_CONNECTIONS
    OPENED_CONNECTIONS = OPENED_CONNECTIONS + 1
    
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)
    

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.error('Article with id "{id}" not exists'.format(id=post_id))  
      return render_template('404.html'), 404
    else:
      app.logger.info('Article "{title}" retrieved!'.format(title=post['title']))  
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('About us accessed')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            app.logger.info('New Article "{title}" created!'.format(title=title))
            return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/healthz')
def healthz():
    response = app.response_class(
            response=json.dumps({'result':'OK - healthy'}),
            status=200,
            mimetype='application/json')
    
    return response


@app.route('/metrics')
def metrics():
    global OPENED_CONNECTIONS
       
    connection = get_db_connection()
    postsCount =  int(connection.execute('SELECT COUNT(*) FROM posts').fetchone()[0])
    connection.close()    

    response = app.response_class(
            response=json.dumps({'post_count': postsCount,'db_connection_count': OPENED_CONNECTIONS}),
            status=200,
            mimetype='application/json'
    )
    
    return response

def setup_logs():
    log_level = logging.DEBUG
    logging.basicConfig(level=log_level)   
    
    log_formatter = logging.Formatter('%(levelname)s:%(name)s:%(asctime)s, %(message)s', '%d/%m/%Y, %H:%M:%S')

    errorHandler = logging.StreamHandler(sys.stderr)     
    errorHandler.setLevel(logging.ERROR)   
    stdHandler = logging.StreamHandler(sys.stdout)         
    stdHandler.setLevel(log_level)

    logger = app.logger
    logger.addHandler(errorHandler)    
    logger.addHandler(stdHandler)    
    logger.propagate  = False

    for handler in logger.handlers:    
        handler.setFormatter(log_formatter)    
    

# start the application on port 3111
if __name__ == '__main__':
   setup_logs()
   app.run(host='0.0.0.0', port='3111')
