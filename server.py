#!/usr/bin/env python3

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, url_for

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)



# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "ps3399"
DB_PASSWORD = "db4111"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}/w4111"

#%env DATABASE_URI=postgresql://ps3399:db4111@w4111.cisxo09blonu.us-east-1.rds.amazonaws.com/w4111


#DATABASEURI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}/proj1part2?options=-csearch_path%3Dpublic"



#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)

########Tests Start#############################
# Query a small sample from the Users table
try:
    with engine.connect() as conn:
        print("Querying Users table...")
        result = conn.execute(text("SELECT * FROM ps3399.test LIMIT 5"))
        users = result.fetchall()
        print("Sample data from Users table:")
        for user in users:
            print(user)  # Print each row in the terminal
except Exception as e:
    print(f"An error occurred while querying Users table: {e}")


# Here we create a test table and insert some values in it

try:
    with engine.connect() as conn:
        print("Dropping table if it exists...")
        conn.execute(text("DROP TABLE IF EXISTS ps3399.test;"))
        print("Creating table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ps3399.test (
                id serial PRIMARY KEY,
                name text
            );
        """))
        conn.commit()  # Commit the transaction
        print("Inserting test data...")
        conn.execute(text("""
            INSERT INTO ps3399.test (name) VALUES
            ('grace hopper'),
            ('alan turing'),
            ('ada lovelace');
        """))
        conn.commit()  # Commit the transaction again after inserting
        print("Table creation and data insertion successful!")
except Exception as e:
    print(f"An error occurred: {e}")


    
######## Start and End Stuff #############################

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

######## HTML interaction #############################

#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def home():
    return render_template("home.html")
    
@app.route('/create_account')
def create_account():
    return "Create Account Page"  # Temporary response for testing
  # Ensure this template exists, or replace with a simple response for now

@app.route('/login')
def login():
    return render_template("login.html")  # Replace with a valid template or a simple response for now

@app.route('/check_login', methods=['GET', 'POST'])
def check_login():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form['password']

        # Query to check for matching username and password
        query = text("SELECT * FROM ps3399.users WHERE username = :username AND password = :password")
        result = g.conn.execute(query, {"username": username, "password": password}).fetchone()

        # Check if a match was found
        if result:
            # Redirect to the user home page if credentials match
            return redirect(url_for('user_home', username=username))
        else:
            # Show an error message if credentials are incorrect
            error = "Incorrect username or password"
            return render_template('login.html', error=error)

    # Render login form if method is GET
    return render_template("login.html")

@app.route('/user_home')
def user_home():
    username = request.args.get('username')
    if not username:
        return redirect(url_for('login'))  # Redirect to login if not logged in
        
    print("username:", username)

    
    # Sample query to retrieve the user's previous games
    previous_games_query = """
    SELECT u1.Username AS Player2, u2.Username AS Player1, a1.Name AS Start_point, a2.Name AS End_point,
           CASE WHEN g.Finished THEN 'Finished' ELSE 'Quit' END AS Status,
           g.Game_id, u1.User_id AS User1_id, u2.User_id AS User2_id, g.Finished
    FROM Games g
    JOIN Plays p1 ON g.Game_id = p1.Game_id
    JOIN Users u1 ON p1.User_id = u1.User_id
    JOIN Plays p2 ON g.Game_id = p2.Game_id
    JOIN Users u2 ON p2.User_id = u2.User_id
    JOIN Actors a1 ON g.Start_point = a1.Actor_id
    JOIN Actors a2 ON g.End_point = a2.Actor_id
    WHERE u2.Username = :username
      AND u1.Username != :username
    """

    # Execute query with a placeholder for `login_username`
    previous_games = g.conn.execute(text(previous_games_query), {"username": username}).fetchall()

    # Sample query to retrieve available lobbies
    available_lobbies_query = """
    SELECT Lobby_Name AS Lobby_Name, Min_experience_level AS Min_experience_level,
           Time_limit_minutes AS Time_limit_minutes, Lobby_id AS Lobby_id
    FROM Lobbies
    """
    available_lobbies = g.conn.execute(text(available_lobbies_query)).fetchall()

    for game in previous_games:
        print(game)
        
    


    # Render template with retrieved data
    return render_template("user_home.html", previous_games=previous_games, available_lobbies=available_lobbies)

# Route to handle lobby joining
@app.route('/join_lobby/<int:lobby_id>')
def join_lobby(lobby_id):
    # Handle joining the lobby (insert into database, etc.)
    # Redirect back to user_home or display success message
    return redirect(url_for('user_home'))
    
# Route to handle lobby joining
@app.route('/game_info/<int:game_id>')
def game_info(game_id):
    # Handle joining the lobby (insert into database, etc.)
    # Redirect back to user_home or display success message
    return redirect(url_for('user_home'))



@app.route('/names')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print(request.args)


  #
  # example of a database query
  #
  print("Starting index route...")
  try:
        # Attempting database query without `text()`
        print("Querying database for names...")
        print("Type of g.conn:", type(g.conn))
        cursor = g.conn.execute(text("SELECT name FROM ps3399.test"))
        #names = [result['name'] for result in cursor]
        names = [result[0] for result in cursor]  # Access the 'name' column by index
        cursor.close()
        print("Names retrieved from database:", names)
  except Exception as e:
        # If an error occurs, print it for debugging
        print(f"Error during database query: {e}")
        names = []  # Fallback in case of error

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
@app.route('/another')
def another():
  return render_template("anotherfile.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  print(name)
  cmd = 'INSERT INTO test(name) VALUES (:name1), (:name2)';
  g.conn.execute(text(cmd), name1 = name, name2 = name);
  return redirect('/')


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
