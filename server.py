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
## Query a small sample from the Users table
#try:
#    with engine.connect() as conn:
#        print("Querying Users table...")
#        result = conn.execute(text("SELECT * FROM ps3399.test LIMIT 5"))
#        users = result.fetchall()
#        print("Sample data from Users table:")
#        for user in users:
#            print(user)  # Print each row in the terminal
#except Exception as e:
#    print(f"An error occurred while querying Users table: {e}")
#
#
## Here we create a test table and insert some values in it
#
#try:
#    with engine.connect() as conn:
#        print("Dropping table if it exists...")
#        conn.execute(text("DROP TABLE IF EXISTS ps3399.test;"))
#        print("Creating table...")
#        conn.execute(text("""
#            CREATE TABLE IF NOT EXISTS ps3399.test (
#                id serial PRIMARY KEY,
#                name text
#            );
#        """))
#        conn.commit()  # Commit the transaction
#        print("Inserting test data...")
#        conn.execute(text("""
#            INSERT INTO ps3399.test (name) VALUES
#            ('grace hopper'),
#            ('alan turing'),
#            ('ada lovelace');
#        """))
#        conn.commit()  # Commit the transaction again after inserting
#        print("Table creation and data insertion successful!")
#except Exception as e:
#    print(f"An error occurred: {e}")


    
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
            user_id = result[0]
            print(f"Redirecting to user_home with username: {username}, user_id: {user_id}")
            return redirect(url_for('user_home', username=username, user_id = user_id))
        else:
            # Show an error message if credentials are incorrect
            error = "Incorrect username or password"
            return render_template('login.html', error=error)

    # Render login form if method is GET
    return render_template("login.html")

@app.route('/user_home')
def user_home():
    username = request.args.get('username')
    user_id = request.args.get('user_id')
    message = request.args.get('message')  # These will be None if not passed
    message_lobby_id = request.args.get('message_lobby_id')
    
    print(f"Username: {username}, User ID: {user_id}, Message: {message}, Message Lobby ID: {message_lobby_id}")

    # Debugging print to check the extracted username
    if username:
        print(f"Extracted username: {username}")
        print(f"Extracted user_id: {user_id}")
    else:
        print("No username found. Redirecting to login.")
        return redirect(url_for('login'))  # Redirect to login if not logged in

        

    
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

 
        
    # Render template with retrieved data
    return render_template(
    "user_home.html",
    previous_games=previous_games,
    available_lobbies=available_lobbies,
    username=username,
    user_id=user_id,
    message=message,
    message_lobby_id=message_lobby_id
)


# Route to handle lobby joining
@app.route('/join_lobby/<int:lobby_id>')
def join_lobby(lobby_id):
    # Get the user's ID and username from the request
    user_id = request.args.get('user_id')
    username = request.args.get('username')  # Capture the username

    # Query the user's experience level
    user_experience_query = """
    SELECT experience_level
    FROM users
    WHERE user_id = :user_id;
    """
    user_experience = g.conn.execute(text(user_experience_query), {"user_id": user_id}).fetchone()
    
    if username:
        print(f"Lobby username: {username}")
    else:
        print("No lobby username found. Redirecting to login.")
        return redirect(url_for('login'))  # Redirect to login if not logged in


    if not user_experience:
        # Handle case where user ID is invalid
        return redirect(url_for('user_home', user_id=user_id, username=username, message="User not found.", message_lobby_id=lobby_id ))

    # Extract the user's experience level
    user_experience_level = user_experience[0]

    # Query the lobby's minimum experience level
    lobby_experience_query = """
    SELECT min_experience_level
    FROM lobbies
    WHERE lobby_id = :lobby_id;
    """
    lobby_experience = g.conn.execute(text(lobby_experience_query), {"lobby_id": lobby_id}).fetchone()

    if not lobby_experience:
        # Handle case where lobby ID is invalid
        return redirect(url_for('user_home', user_id=user_id, username=username, message="Lobby not found.", message_lobby_id = lobby_id))

    # Extract the lobby's minimum experience level
    min_experience_level = lobby_experience[0]

    # Check if the user has enough experience
    if user_experience_level < min_experience_level:
        # Redirect back to user home with an insufficient experience message
        return redirect(url_for('user_home', user_id=user_id, username=username, message="Insufficient Experience", message_lobby_id = lobby_id))

    # Query to check if the lobby already has a user
    existing_user_query = """
    SELECT user_id
    FROM users
    WHERE lobby_id = :lobby_id;
    """
    existing_users = g.conn.execute(text(existing_user_query), {"lobby_id": lobby_id}).fetchall()

    if not existing_users:
        # Update the user's lobby ID if the lobby is empty
        update_lobby_query = """
        UPDATE users
        SET lobby_id = :lobby_id
        WHERE user_id = :user_id;
        """
        g.conn.execute(text(update_lobby_query), {"lobby_id": lobby_id, "user_id": user_id})
        return redirect(url_for('user_home', user_id=user_id, username=username, message="Waiting", message_lobby_id = lobby_id))
    else:
        # Take the first user in the lobby and prepare for game start (dummy for now)
        other_user_id = existing_users[0][0]
        query = text("""
        UPDATE ps3399.Users
        SET Lobby_id = NULL
        WHERE User_id = :other_user_id
        """)

        # Execute the query, replacing `other_user_id` with the actual user ID, this will remove the player that was waiting from the lobby
        g.conn.execute(query, {"other_user_id": other_user_id})
        
        return redirect(url_for('start_game', user_id=user_id, username=username, other_user_id=other_user_id))


    
@app.route('/game_info/<int:game_id>')
def game_info(game_id):
    # Query to get the moves in the chain
    chain_query = """
    SELECT actors.name AS actor_name, actors.picture AS actor_picture,
           movies.title AS movie_title, movies.poster AS movie_poster,
           chains.move_number, games.finished
    FROM chains
    JOIN acts_in_connections ON chains.connection_id = acts_in_connections.connection_id
    JOIN movies ON movies.movie_id = acts_in_connections.movie_id
    JOIN actors ON actors.actor_id = acts_in_connections.actor_id
    JOIN games ON games.game_id = chains.game_id
    WHERE chains.game_id = :game_id
    ORDER BY chains.move_number;
    """
    
    # Execute the chain query
    chain_results = g.conn.execute(text(chain_query), {"game_id": game_id}).fetchall()

    # Query to get the start and end points
    start_end_query = """
    SELECT a1.name AS start_actor_name, a1.picture AS start_actor_picture,
           a2.name AS end_actor_name, a2.picture AS end_actor_picture
    FROM games
    JOIN actors AS a1 ON games.start_point = a1.actor_id
    JOIN actors AS a2 ON games.end_point = a2.actor_id
    WHERE games.game_id = :game_id;
    """
    
    # Execute the start and end query
    start_end_results = g.conn.execute(text(start_end_query), {"game_id": game_id}).fetchone()

    # Check if moves exist
    has_moves = bool(chain_results)

    # Render the template with both queries' results and the flag
    return render_template(
        "game_info.html",
        chain=chain_results,
        start_end=start_end_results,
        has_moves=has_moves
    )






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
