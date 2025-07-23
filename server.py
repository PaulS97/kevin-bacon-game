
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
import signal
import sys
from sqlalchemy import *
from sqlalchemy.sql import text
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import IntegrityError
from flask import Flask, request, render_template, g, redirect, Response, url_for, jsonify, flash
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
import pandas as pd
import networkx as nx
import pickle

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_secret_key")

socketio = SocketIO(app, cors_allowed_origins="*")




# Graceful shutdown on Ctrl+C
def shutdown_server():
    print("Shutting down server...")
    try:
        # Notify all connected clients
        socketio.emit("server_shutdown", {"message": "The server is shutting down. Please reconnect later."}, broadcast=True)

        # Use os._exit() for an immediate exit
        import os
        os._exit(0)  # Immediately terminates the process
    except Exception as e:
        print(f"Error during shutdown: {e}")
        os._exit(1)  # Use exit code 1 for errors


signal.signal(signal.SIGINT, shutdown_server)




# Attach signal handlers for SIGINT and SIGTERM
signal.signal(signal.SIGINT, shutdown_server)  # For Ctrl+C
signal.signal(signal.SIGTERM, shutdown_server)  # For termination

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

with engine.begin() as conn:
    conn.execute(text("UPDATE Users SET Lobby_id = NULL"))
    print("All users removed from lobbies at startup.")


# Build weighted bipartite graph from SQL
def build_weighted_graph(engine):
    query = """
        SELECT 
            ac.actor_id,
            ac.movie_id,
            (1.0 / NULLIF((a.weighted_centrality + m.imdb_vote_count) / 2.0, 0)) AS weight
        FROM acts_in_connections ac
        JOIN actors a ON ac.actor_id = a.actor_id
        JOIN movies m ON ac.movie_id = m.movie_id
        WHERE a.weighted_centrality IS NOT NULL AND m.imdb_vote_count IS NOT NULL
    """

    connections_df = pd.read_sql(query, engine)

    # Add prefixes to distinguish node types (avoid ID collisions)
    connections_df["actor_node"] = "actor_" + connections_df["actor_id"].astype(str)
    connections_df["movie_node"] = "movie_" + connections_df["movie_id"].astype(str)

    # Create the graph
    G = nx.Graph()
    for _, row in connections_df.iterrows():
        G.add_edge(row["actor_node"], row["movie_node"], weight=row["weight"])

    return G

#G = build_weighted_graph(engine)
GRAPH_PATH = "graph_cache.pkl"

def get_or_build_graph(engine):
    if os.path.exists(GRAPH_PATH):
        print("Loading graph from cache...")
        with open(GRAPH_PATH, "rb") as f:
            return pickle.load(f)
    else:
        print("Building graph from scratch...")
        G = build_weighted_graph(engine)
        with open(GRAPH_PATH, "wb") as f:
            pickle.dump(G, f)
        return G

G = get_or_build_graph(engine)




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
    

@app.route('/login')
def login():
    return render_template("login.html")  # Replace with a valid template or a simple response for now

@app.route("/create_account")
def create_account_form():
    return render_template("create_account.html")

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
    user_id = request.args.get('user_id')
    message = request.args.get('message')  # These will be None if not passed
    message_lobby_id = request.args.get('message_lobby_id')
    username = request.args.get('username')

    
    print(f"Username: {username}, User ID: {user_id}, Message: {message}, Message Lobby ID: {message_lobby_id}")

    # Debugging print to check the extracted username
    if user_id:
        print(f"Extracted user_id: {user_id}")
    else:
        print("No user_id found. Redirecting to login.")
        return redirect(url_for('home'))  # Redirect to login if not logged in

        

    
    # Sample query to retrieve the user's previous games
    previous_games_query = """
    SELECT
        COALESCE(u1.Username, '—') AS Player2,
        u2.Username AS Player1,
        a1.Name AS Start_point,
        a2.Name AS End_point,
        CASE WHEN g.Finished THEN 'Finished' ELSE 'Quit' END AS Status,
        g.Game_id,
        u1.User_id AS User1_id,
        u2.User_id AS User2_id,
        g.Finished
    FROM Games g
    JOIN Plays p1 ON g.Game_id = p1.Game_id
    JOIN Users u2 ON p1.User_id = u2.User_id
    LEFT JOIN Plays p2 ON g.Game_id = p2.Game_id AND p2.User_id != u2.User_id
    LEFT JOIN Users u1 ON p2.User_id = u1.User_id
    JOIN Actors a1 ON g.Start_point = a1.Actor_id
    JOIN Actors a2 ON g.End_point = a2.Actor_id
    WHERE u2.User_id = :user_id
    """

    # Execute query with a placeholder for `login_username`
    previous_games = g.conn.execute(text(previous_games_query), {"user_id": user_id}).fetchall()

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




@socketio.on("join_lobby")
def handle_join_lobby(data):
    lobby_id = data["lobby_id"]
    user_id = data["user_id"]
    room_name = f"lobby_{lobby_id}"
    personal_room = f"user_{user_id}"

    join_room(room_name)
    join_room(personal_room)

    print(f"User {user_id} joined lobby {lobby_id}")
    
    with engine.connect() as connection:
        trans = connection.begin()
        try:
            room_members = list(socketio.server.manager.get_participants("/", room_name))
            print(f"Current participants in {room_name}: {room_members}")

            # Update user's lobby_id in DB
            update_user_lobby = text("""
                UPDATE Users SET Lobby_id = :lobby_id WHERE User_id = :user_id
            """)
            connection.execute(update_user_lobby, {"lobby_id": lobby_id, "user_id": user_id})
            
            if len(room_members) >= 2:
                game_id = create_game(connection, lobby_id, trans)
                other_user_id = get_other_user_in_room(connection, lobby_id, user_id)
                if other_user_id is None:
                    raise ValueError(f"Could not find other user in lobby {lobby_id}")
                
                add_players_to_game(connection, game_id, user_id, other_user_id, trans)

                print(f"Emitting start_game to users {user_id} and {other_user_id} for game {game_id}")

                socketio.emit(
                    "start_game",
                    {"game_id": game_id, "user1_id": user_id, "user2_id": other_user_id},
                    room=f"user_{user_id}"
                )
                socketio.emit(
                    "start_game",
                    {"game_id": game_id, "user1_id": user_id, "user2_id": other_user_id},
                    room=f"user_{other_user_id}"
                )
            else:
                emit("waiting", {"message": "Waiting for another player"}, room=room_name)

            trans.commit()
        except Exception as e:
            print(f"Error during join lobby: {e}")
            trans.rollback()




def get_other_user_in_room(connection, lobby_id, current_user_id):
    """Fetch the other user's ID in the same lobby."""
    print(f"Debug: lobby_id={lobby_id}, current_user_id={current_user_id}")
    try:
        query = text("""
            SELECT User_id
            FROM Users
            WHERE Lobby_id = :lobby_id AND User_id != :current_user_id
        """)
        result = connection.execute(query, {"lobby_id": lobby_id, "current_user_id": current_user_id}).fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"Error fetching other user in lobby: {e}")
        return None


def create_game(connection, lobby_id, trans):
    try:
        max_game_query = text("SELECT COALESCE(MAX(Game_id), 0) + 1 AS new_game_id FROM Games")
        new_game_id = connection.execute(max_game_query).fetchone()[0]

        time_limit_query = text("SELECT Time_limit_minutes FROM Lobbies WHERE Lobby_id = :lobby_id")
        time_limit = connection.execute(time_limit_query, {"lobby_id": lobby_id}).fetchone()[0]

        insert_game_query = text("""
            INSERT INTO Games (Game_id, Time_limit_minutes, Finished)
            VALUES (:game_id, :time_limit, FALSE)
        """)
        connection.execute(insert_game_query, {"game_id": new_game_id, "time_limit": time_limit})
        print(f"Game {new_game_id} inserted successfully.")
        return new_game_id
    except Exception as e:
        print(f"Error inserting game: {e}")
        trans.rollback()
        raise



def add_players_to_game(connection, game_id, user1_id, user2_id, trans):
    try:
        insert_plays_query = text("""
            INSERT INTO Plays (User_id, Game_id)
            VALUES (:user_id, :game_id)
        """)
        connection.execute(insert_plays_query, {"user_id": user1_id, "game_id": game_id})
        connection.execute(insert_plays_query, {"user_id": user2_id, "game_id": game_id})

        reset_lobby_query = text("""
            UPDATE Users SET Lobby_id = NULL WHERE User_id IN (:user1_id, :user2_id)
        """)
        connection.execute(reset_lobby_query, {"user1_id": user1_id, "user2_id": user2_id})

        print(f"Players {user1_id} and {user2_id} added to game {game_id} and removed from lobby.")
    except Exception as e:
        print(f"Error adding players to game: {e}")
        trans.rollback()
        raise

@socketio.on("leave_lobby")
def handle_leave_lobby(data):
    user_id = request.args.get("user_id")
    lobby_id = request.args.get("lobby_id")

    print(f"User {user_id} left lobby {lobby_id}.")

    if user_id and lobby_id:
        try:
            leave_room(f"lobby_{lobby_id}")
            with engine.begin() as conn:
                conn.execute(text("UPDATE Users SET Lobby_id = NULL WHERE User_id = :uid"), {"uid": user_id})
        except Exception as e:
            print(f"Error during leave_lobby: {e}")



@app.route("/gameplay/<int:game_id>")
def gameplay(game_id):
    # Extract user_id from the query parameters
    user_id = request.args.get("user_id")
    if not user_id:
        return "Missing user_id", 400

    # Fetch game details as a mapping
    game_query = text("SELECT * FROM Games WHERE game_id = :game_id")
    game = g.conn.execute(game_query, {"game_id": game_id}).mappings().fetchone()
    num_players = game["num_players"]


    if not game:
        return "Game not found", 404

    # Fetch players and determine roles
    players_query = text("SELECT user_id FROM Plays WHERE game_id = :game_id ORDER BY user_id")
    players = g.conn.execute(players_query, {"game_id": game_id}).mappings().fetchall()

    if len(players) < num_players:
        return "Players not properly initialized", 400

    if(num_players==1):
        start_setter = players[0]["user_id"]
        end_setter = players[0]["user_id"]
    else:
        start_setter = players[0]["user_id"]
        end_setter = players[1]["user_id"]

        
        


    print(f"[DEBUG] user_id: {user_id}, start_setter: {start_setter}, end_setter: {end_setter}")
    print(f"[DEBUG] Game Info: {game}")


    if int(user_id) == start_setter and not game["start_point"]:
        next_action = "start_point"
    elif int(user_id) == end_setter and not game["end_point"]:
        next_action = "end_point"
    elif int(user_id) != start_setter and int(user_id) != end_setter:
        return "Invalid user", 400
    else:
        next_action = "play_game"
    

    # Include start and end point in the response
    start_point = game["start_point"]
    end_point = game["end_point"]

    return render_template(
        "gameplay.html",
        game=game,
        user_id=user_id,
        start_point=start_point,
        end_point=end_point,
        next_action=next_action,
    )





@app.route("/set_end_point/<int:game_id>", methods=["POST"])
def set_end_point(game_id):
    user_id = request.args.get("user_id")
    actor_id = request.form.get("move_id")

    if not actor_id:
        flash("Please select an actor before submitting.", "error")
        return redirect(f"/gameplay/{game_id}?user_id={user_id}")

    try:
        with engine.connect() as connection:
            update_game_query = text("UPDATE Games SET end_point = :actor_id WHERE game_id = :game_id")
            connection.execute(update_game_query, {"actor_id": actor_id, "game_id": game_id})
            connection.commit()

            game_query = text("SELECT * FROM Games WHERE game_id = :game_id")
            game = connection.execute(game_query, {"game_id": game_id}).mappings().fetchone()

        if process_ready_players(game_id):
            return redirect(f"/game_stage/{game_id}?user_id={user_id}&start_point={game['start_point']}&end_point={game['end_point']}")
        else:
            return redirect(f"/gameplay/{game_id}?user_id={user_id}")

    except IntegrityError:
        flash("That actor is already being used as the start point in this game.", "error")
        return redirect(f"/gameplay/{game_id}?user_id={user_id}")



@app.route("/set_start_point/<int:game_id>", methods=["POST"])
def set_start_point(game_id):
    user_id = request.args.get("user_id")
    actor_id = request.form.get("move_id")

    if not actor_id:
        flash("Please select an actor before submitting.", "error")
        return redirect(f"/gameplay/{game_id}?user_id={user_id}")

    try:
        with engine.connect() as connection:
            update_game_query = text("UPDATE Games SET start_point = :actor_id WHERE game_id = :game_id")
            connection.execute(update_game_query, {"actor_id": actor_id, "game_id": game_id})
            connection.commit()

            game_query = text("SELECT * FROM Games WHERE game_id = :game_id")
            game = connection.execute(game_query, {"game_id": game_id}).mappings().fetchone()

        if process_ready_players(game_id):
            return redirect(f"/game_stage/{game_id}?user_id={user_id}&start_point={game['start_point']}&end_point={game['end_point']}")
        else:
            return redirect(f"/gameplay/{game_id}?user_id={user_id}")

    except IntegrityError:
        flash("That actor is already being used as the end point in this game.", "error")
        return redirect(f"/gameplay/{game_id}?user_id={user_id}")





@socketio.on("start_game")
def handle_start_game(data):
    lobby_id = data["lobby_id"]
    game_id = data["game_id"]

    # Emit to all players in the room that the game has started
    emit("game_started", {"game_id": game_id}, room=f"lobby_{lobby_id}")
    print(f"Game {game_id} started for lobby {lobby_id}")


def process_ready_players(game_id):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT Start_point, End_point FROM Games WHERE Game_id = :gid
        """), {"gid": game_id}).fetchone()

        start_point, end_point = result if result else (None, None)

        if start_point and end_point:
            players = conn.execute(text("""
                SELECT User_id FROM Plays WHERE Game_id = :gid
            """), {"gid": game_id}).fetchall()

            for row in players:
                player_id = row[0]
                socketio.emit(
                    "start_game",
                    {
                        "game_id": game_id,
                        "user_id": player_id,
                        "start_point": start_point,
                        "end_point": end_point
                    },
                    room=f"game_{game_id}_player_{player_id}",
                    namespace="/gameplay"
                )
            return True  # ✅ Game was ready and start_game was emitted
        else:
            return False  # ❌ Still waiting for start or end



@app.route("/game_stage/<int:game_id>")
def game_stage(game_id):
    # Extract user_id from query parameters
    user_id = request.args.get("user_id")
    start_point = request.args.get("start_point")
    end_point = request.args.get("end_point")
    if not user_id:
        return "Missing user_id", 400

    # Fetch game details
    game_query = text("SELECT * FROM Games WHERE game_id = :game_id")
    game = g.conn.execute(game_query, {"game_id": game_id}).mappings().fetchone()
    num_players = game["num_players"]

    # After querying game
    if game["finished"]:
        return redirect(f"/game_info/{game_id}?user_id={user_id}")


    if num_players == 1:
        print("Solo game detected")
    else:
        print("Multiplayer game")


    if not game:
        return "Game not found", 404

    # Fetch the start and end point actor names and pictures
    start_actor_query = text("SELECT name, picture FROM Actors WHERE actor_id = :actor_id")
    start_actor_result = g.conn.execute(start_actor_query, {"actor_id": game["start_point"]}).mappings().fetchone()
    start_actor = start_actor_result["name"]
    start_actor_picture = start_actor_result["picture"]

    end_actor_query = text("SELECT name, picture FROM Actors WHERE actor_id = :actor_id")
    end_actor_result = g.conn.execute(end_actor_query, {"actor_id": game["end_point"]}).mappings().fetchone()
    end_actor = end_actor_result["name"]
    end_actor_picture = end_actor_result["picture"]

    # Fetch game players
    players_query = text("SELECT user_id FROM Plays WHERE game_id = :game_id ORDER BY user_id")
    players = g.conn.execute(players_query, {"game_id": game_id}).mappings().fetchall()
    if len(players) != num_players:
        return "Invalid number of players in the game", 400

    player_ids = [p["user_id"] for p in players]
    player_turn = player_ids[0]


    move_type = "movie"
    turn_number = 0
    player_turn = player_ids[0]


    print(f"Debug: Calculated player_turn={player_turn}, current user_id={user_id}")
    print(f"Debug: move_type={move_type}, turn_number={turn_number}")
    print(f"Debug: Rendering game_stage with start_actor={start_actor}, end_actor={end_actor}, user_id={user_id}, player_turn={player_turn}")

    # Render the game_stage template
    return render_template(
        "game_stage.html",
        game=game,
        user_id=user_id,
        player_turn=player_turn,
        move_type=move_type,
        last_move_id=game["start_point"], 
        start_actor=start_actor,
        start_actor_picture=start_actor_picture,
        end_actor=end_actor,
        end_actor_picture=end_actor_picture,
        num_players = num_players
    )




@socketio.on("make_move", namespace="/game_stage")
def handle_make_move(data):
    user_id = data.get("user_id")
    game_id = data.get("game_id")
    move = data.get("move")
    move_id = data.get("move_id")
    move_type = data.get("move_type")
    last_move_id = data.get("last_move_id")

    if not move_id:
        socketio.emit("game_error", {"message": "Invalid move: no ID selected."}, room=f"game_{game_id}_player_{user_id}", namespace="/game_stage")
        return


    print(f"Received move from user {user_id} for game {game_id}: {move}, move_type: {move_type}, move_id: {move_id}, last_move_id: {last_move_id}")

    # Use an explicit connection to handle database operations
    with engine.connect() as connection:
       
        current_move_id = move_id

        # Validate the connection exists
        connection_query = text("""
            SELECT connection_id FROM Acts_In_Connections
            WHERE (actor_id = :actor_id AND movie_id = :movie_id)
            OR (actor_id = :movie_id AND movie_id = :actor_id)
        """)
        connection_result = connection.execute(connection_query, {
            "actor_id": current_move_id if move_type == "actor" else last_move_id,
            "movie_id": current_move_id if move_type == "movie" else last_move_id
        }).mappings().fetchone()

        if not connection_result:
            print("Invalid connection. This move is not valid.")
            socketio.emit("game_error", {
                "message": "Invalid connection. Please try again."
            }, room=f"game_{game_id}_player_{user_id}", namespace="/game_stage")
            return


        connection_id = connection_result["connection_id"]

        try:
            # Attempt to insert move
            insert_move_query = text("""
                INSERT INTO Chains (connection_id, game_id, user_id, move_number)
                VALUES (:connection_id, :game_id, :user_id, (
                    SELECT COALESCE(MAX(move_number), 0) + 1 FROM Chains WHERE game_id = :game_id
                ))
            """)
            connection.execute(insert_move_query, {
                "connection_id": connection_id,
                "game_id": game_id,
                "user_id": user_id
            })
            connection.commit()

        except IntegrityError as e:
            # Duplicate connection (already used in this game)
            print("Duplicate move error:", e)
            socketio.emit("game_error", {
                "message": "Invalid move: that actor/movie connection has already been used."
            }, room=f"game_{game_id}_player_{user_id}", namespace="/game_stage")
            connection.rollback()  # always rollback on failed insert
            return
        

        print("Move successfully recorded in Chains.")
        
        
        
        # Check if game is finished
        game_query = text("SELECT * FROM Games WHERE game_id = :game_id")
        game = connection.execute(game_query, {"game_id": game_id}).mappings().fetchone()


        num_players = game["num_players"]


        # ✅ Debug statements to verify condition logic
        print(f"[DEBUG] move_type: {move_type}")
        print(f"[DEBUG] current_move_id: {current_move_id}")
        print(f"[DEBUG] expected end_point: {game['end_point']}")

        print(f"[DEBUG] current_move_id type: {type(current_move_id)}")
        print(f"[DEBUG] end_point type: {type(game['end_point'])}")


        if move_type == "actor" and int(current_move_id) == game["end_point"]:
            print("Game over! End point reached.")
            
            # Update the Games table to mark the game as finished
            update_game_query = text("UPDATE Games SET Finished = TRUE WHERE game_id = :game_id")
            connection.execute(update_game_query, {"game_id": game_id})
            connection.commit()

            # Notify players that the game is over
            socketio.emit("game_over", {"game_id": game_id}, room=f"game_{game_id}", namespace="/game_stage")
            return
        
        # Log game_id before using it in the query
        print(f"Debug: game_id before query = {game_id}")

        # Fetch game players to determine the next turn
        players_query = text("SELECT user_id FROM Plays WHERE game_id = :game_id ORDER BY user_id")
        players = connection.execute(players_query, {"game_id": game_id}).mappings().fetchall()
        if len(players) !=  num_players:
            print("Invalid number of players in the game.")
            socketio.emit("game_error", {"message": "Game configuration error."}, room=f"game_{game_id}_player_{user_id}", namespace="/game_stage")
            return

        # players is a list of dicts: [{"user_id": ...}, ...]
        print(f"[DEBUG] Raw players list from DB: {players}")

        player_ids = [p["user_id"] for p in players]
        num_players = len(player_ids)
        print(f"[DEBUG] Extracted player_ids: {player_ids}")
        print(f"[DEBUG] Number of players in game: {num_players}")

        # Fetch turn number from game state
        turn_query = text("SELECT COUNT(*) FROM Chains WHERE Game_id = :game_id")
        turn_number = connection.execute(turn_query, {"game_id": game_id}).scalar()
        print(f"[DEBUG] Total moves in Chains for game {game_id}: {turn_number}")

        # Determine next player
        next_player_index = turn_number % num_players
        player_turn = player_ids[next_player_index]

        print(f"[DEBUG] Calculated next_player_index: {next_player_index}")
        print(f"[DEBUG] Assigned player_turn: {player_turn}")


        # Determine the next move type
        next_move_type = "movie" if move_type == "actor" else "actor"

        # Get the image for the current move
        if move_type == "actor":
            image_query = text("SELECT picture FROM Actors WHERE actor_id = :id")
        else:
            image_query = text("SELECT poster FROM Movies WHERE movie_id = :id")

        image_result = connection.execute(image_query, {"id": current_move_id}).fetchone()
        image_url = image_result[0] if image_result else None



        # Include move_type in the game_update emission
        game_update = {
            "game_id": game_id,
            "move": move,
            "last_move_id": current_move_id,
            "player_turn": player_turn,
            "move_type": next_move_type,  # Send the toggled move type
            "image_url": image_url  # 👈 add this line
        }

        print(f"Emitting game_update: {game_update}")
        socketio.emit("game_update", game_update, room=f"game_{game_id}", namespace="/game_stage")



@socketio.on("player_ready_for_moves", namespace="/game_stage")
def player_ready(data):
    user_id = data["user_id"]
    game_id = data["game_id"]

    join_room(f"game_{game_id}_player_{user_id}")

    with engine.connect() as connection:
        game_update = get_current_game_state(game_id, user_id, connection)

        if game_update:
            print(f"Rehydrating user {user_id} with game_update: {game_update}")
            socketio.emit(
                "game_update",
                game_update,
                room=f"game_{game_id}_player_{user_id}",
                namespace="/game_stage"
            )

def get_current_game_state(game_id, user_id, connection):
    # Check if any moves have been made
    chain_check = connection.execute(
        text("SELECT COUNT(*) FROM Chains WHERE game_id = :game_id"),
        {"game_id": game_id}
    ).scalar()

    if chain_check == 0:
        return None  # No moves yet → no need to emit

    # Get latest move from Chains
    last_move = connection.execute(
        text("""
            SELECT connection_id, move_number
            FROM Chains
            WHERE game_id = :game_id
            ORDER BY move_number DESC
            LIMIT 1
        """), {"game_id": game_id}
    ).mappings().fetchone()

    connection_id = last_move["connection_id"]
    move_number = last_move["move_number"]

    # Determine current move type and last_move_id
    is_movie_turn = (move_number % 2 == 1)  # 1, 3, 5... means movie is the current move
    move_type = "actor" if is_movie_turn else "movie"

    acts_row = connection.execute(
        text("""
            SELECT actor_id, movie_id
            FROM Acts_In_Connections
            WHERE connection_id = :connection_id
        """), {"connection_id": connection_id}
    ).mappings().fetchone()

    actor_id = acts_row["actor_id"]
    movie_id = acts_row["movie_id"]

    if is_movie_turn:
        # Current move is a movie → show movie
        movie = connection.execute(
            text("SELECT title, poster FROM Movies WHERE movie_id = :movie_id"),
            {"movie_id": movie_id}
        ).mappings().fetchone()
        move = movie["title"]
        image_url = movie["poster"]
        last_move_id = movie_id  # next move must connect from this actor
    else:
        # Current move is an actor → show actor
        actor = connection.execute(
            text("SELECT name, picture FROM Actors WHERE actor_id = :actor_id"),
            {"actor_id": actor_id}
        ).mappings().fetchone()
        move = actor["name"]
        image_url = actor["picture"]
        last_move_id = actor_id  # next move must connect from this movie

    # Fetch player list to determine whose turn is next
    players = connection.execute(
        text("SELECT user_id FROM Plays WHERE game_id = :game_id ORDER BY user_id"),
        {"game_id": game_id}
    ).mappings().fetchall()

    player_ids = [p["user_id"] for p in players]
    num_players = len(player_ids)

    turn_count = move_number  # 1-based
    next_player_index = turn_count % num_players
    player_turn = player_ids[next_player_index]

    return {
        "game_id": game_id,
        "move": move,
        "last_move_id": last_move_id,
        "player_turn": player_turn,
        "move_type": move_type,
        "image_url": image_url
    }





@socketio.on("connect", namespace="/gameplay")
def handle_gameplay_connect():
    user_id = request.args.get("user_id")
    game_id = request.args.get("game_id")
    if not user_id or not game_id:
        print("Missing user_id or game_id in gameplay socket connection.")
        return
        
    print(f"Connect event received for gameplay: user_id={request.args.get('user_id')}, game_id={request.args.get('game_id')}")

    # Define personal and game-wide rooms
    personal_room = f"game_{game_id}_player_{user_id}"
    game_room = f"game_{game_id}"

    # Leave and rejoin rooms to ensure no duplicates
    leave_room(personal_room)
    join_room(personal_room)
    print(f"User {user_id} joined personal room: {personal_room}")

    leave_room(game_room)
    join_room(game_room)
    print(f"User {user_id} joined game-wide room: {game_room}")

@socketio.on("connect", namespace="/game_stage")
def handle_gamestage_connect():
    user_id = request.args.get("user_id")
    game_id = request.args.get("game_id")
    if not user_id or not game_id:
        print("Missing user_id or game_id in gameplay socket connection.")
        return
        
    print(f"Connect event received for game_stage: user_id={request.args.get('user_id')}, game_id={request.args.get('game_id')}")

    # Define personal and game-wide rooms
    personal_room = f"game_{game_id}_player_{user_id}"
    game_room = f"game_{game_id}"

    # Leave and rejoin rooms to ensure no duplicates
    leave_room(personal_room)
    join_room(personal_room)
    print(f"User {user_id} joined personal room: {personal_room}")

    leave_room(game_room)
    join_room(game_room)
    print(f"User {user_id} joined game-wide room: {game_room}")







@socketio.on("disconnect")
def handle_disconnect():
    user_id = request.args.get("user_id")
    print(f"Socket disconnected for User ID: {user_id}")

    if user_id:
        with engine.begin() as conn:
            conn.execute(text("UPDATE Users SET Lobby_id = NULL WHERE User_id = :uid"), {"uid": user_id})
            print(f"User {user_id} removed from lobby on disconnect.")





    
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

    with engine.connect() as connection:
        # ✅ Get all players and hints used
        result = connection.execute(text("""
            SELECT u.username, p.hints_taken
            FROM Plays p
            JOIN Users u ON p.user_id = u.user_id
            WHERE p.game_id = :game_id
        """), {"game_id": game_id}).mappings().all()

        players_hints = [{"username": row["username"], "hints": row["hints_taken"]} for row in result]



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
    
    #extarct user id
    user_id = request.args.get("user_id")  # Extract user_id from the query parameters
    if not user_id:
        return "Missing user_id", 400
        
     # Fetch username from the database
    user_query = text("SELECT username FROM Users WHERE user_id = :user_id")
    with engine.connect() as connection:
        user_result = connection.execute(user_query, {"user_id": user_id}).mappings().fetchone()
        
    
    if not user_result:
        return "User not found", 404
        
    username = user_result["username"]


    # Render the template with both queries' results and the flag
    return render_template(
        "game_info.html",
        chain=chain_results,
        start_end=start_end_results,
        has_moves=has_moves,
        user_id=user_id,
        username=username,
        game_id = game_id,
        players_hints = players_hints
    )

@app.route("/autocomplete")
def autocomplete():
    q = request.args.get("q", "").lower()
    entity_type = request.args.get("type")

    if not q or entity_type not in ("actor", "movie"):
        return jsonify([])

    if entity_type == "actor":
        query = text("""
            SELECT actor_id as id, name, picture FROM actors
            WHERE LOWER(name) LIKE :pattern
            ORDER BY weighted_centrality DESC
            LIMIT 5
        """)
    else:
        query = text("""
            SELECT
                movie_id as id,
                title || ' (' || EXTRACT(YEAR FROM "release") || ')' AS name,
                poster AS picture
            FROM movies
            WHERE LOWER(title) LIKE :pattern
            ORDER BY imdb_vote_count DESC
            LIMIT 5
        """)


    results = g.conn.execute(query, {"pattern": f"%{q}%"}).mappings().fetchall()
    return jsonify([{"id": r["id"], "name": r["name"], "picture": r["picture"]} for r in results])

@socketio.on("request_hint", namespace="/game_stage")
def handle_request_hint(data):
    user_id = data.get("user_id")
    game_id = data.get("game_id")
    last_move_id = data.get("last_move_id")
    move_type = data.get("move_type")

    print("Received request_hint:", data)


    try:
        with engine.connect() as connection:
            game_query = text("SELECT end_point FROM Games WHERE game_id = :game_id")
            game = connection.execute(game_query, {"game_id": game_id}).mappings().fetchone()
            end_actor_id = game["end_point"]

        source = f"actor_{last_move_id}" if move_type == "movie" else f"movie_{last_move_id}"
        target = f"actor_{end_actor_id}"


        # ✅ Use pruned graph based on current game's chain history
        G_pruned = get_pruned_graph_for_game(engine, G, game_id, source)

        # Find shortest path in filtered graph
        path = nx.shortest_path(G_pruned, source=source, target=target, weight="weight")

        if len(path) < 2:
            raise ValueError("No valid hint path found")

        next_node = path[1]  # First move from current position
        next_type, next_id = next_node.split("_")

        with engine.connect() as connection:
            if next_type == "actor":
                result = connection.execute(
                    text("SELECT name, picture FROM Actors WHERE actor_id = :id"),
                    {"id": int(next_id)}
                ).mappings().fetchone()
            else:
                result = connection.execute(
                    text("SELECT title AS name, poster AS picture FROM Movies WHERE movie_id = :id"),
                    {"id": int(next_id)}
                ).mappings().fetchone()

        if not result:
            raise ValueError("Hint target not found in database")

        # Increment Hints_taken in Plays
        with engine.begin() as connection:
            connection.execute(
                text("""
                    UPDATE Plays
                    SET Hints_taken = COALESCE(Hints_taken, 0) + 1
                    WHERE user_id = :user_id AND game_id = :game_id
                """),
                {"user_id": user_id, "game_id": game_id}
            )


        socketio.emit("hint_response", {
            "id": int(next_id),
            "name": result["name"],
            "picture": result["picture"]
        }, room=f"game_{game_id}_player_{user_id}", namespace="/game_stage")



    except Exception as e:
        print("Hint error:", e)
        socketio.emit("hint_response", {
            "error": "Could not generate hint. Try again."
        }, room=f"game_{game_id}_player_{user_id}", namespace="/game_stage")


def get_pruned_graph_for_game(engine, base_graph, game_id, source_node):
    with engine.connect() as conn:
        # 1. Get all actor/movie IDs from the chain for this game
        query = text("""
            SELECT a.actor_id, a.movie_id
            FROM Chains c
            JOIN Acts_In_Connections a ON c.connection_id = a.connection_id
            WHERE c.game_id = :game_id
        """)
        result = conn.execute(query, {"game_id": game_id}).fetchall()

    # 2. Build set of graph node IDs to exclude
    used_nodes = set()
    for row in result:
        used_nodes.add(f"actor_{row.actor_id}")
        used_nodes.add(f"movie_{row.movie_id}")

    # 3. Don't remove the current node (we're trying to expand from it)
    used_nodes.discard(source_node)

    # 4. Copy the graph and remove edges connected to any used node
    G_temp = base_graph.copy()
    edges_to_remove = [
        (u, v) for u, v in G_temp.edges
        if u in used_nodes or v in used_nodes
    ]
    G_temp.remove_edges_from(edges_to_remove)

    return G_temp



@app.route("/alternate_chain/<int:game_id>")
def alternate_chain(game_id):
    user_id = request.args.get("user_id")
    username = request.args.get("username")

    # Step 1: Fetch start and end points
    game_query = text("SELECT start_point, end_point FROM Games WHERE game_id = :game_id")
    game = g.conn.execute(game_query, {"game_id": game_id}).mappings().fetchone()
    if not game:
        return "Game not found", 404

    start_node = f"actor_{game['start_point']}"
    end_node = f"actor_{game['end_point']}"

    try:
        path = nx.shortest_path(G, source=start_node, target=end_node, weight="weight")
    except nx.NetworkXNoPath:
        return "No alternate path found", 404

    # Break into alternating list of movies/actors
    alt_chain = []
    for i in range(1, len(path) - 1):
        node = path[i]
        node_type, node_id = node.split("_")
        if node_type == "movie":
            movie_query = text("SELECT title, poster FROM Movies WHERE movie_id = :id")
            result = g.conn.execute(movie_query, {"id": int(node_id)}).mappings().fetchone()
            alt_chain.append({"type": "movie", "title": result["title"], "poster": result["poster"]})
        else:
            actor_query = text("SELECT name, picture FROM Actors WHERE actor_id = :id")
            result = g.conn.execute(actor_query, {"id": int(node_id)}).mappings().fetchone()
            alt_chain.append({"type": "actor", "name": result["name"], "picture": result["picture"]})

    # Also get start and end actor info
    start_actor = g.conn.execute(
        text("SELECT name, picture FROM Actors WHERE actor_id = :id"),
        {"id": game["start_point"]}).mappings().fetchone()
    end_actor = g.conn.execute(
        text("SELECT name, picture FROM Actors WHERE actor_id = :id"),
        {"id": game["end_point"]}).mappings().fetchone()

    return render_template(
        "alternate_chain.html",
        start_actor=start_actor,
        end_actor=end_actor,
        chain=alt_chain,
        user_id=user_id,
        username=username,
        game_id=game_id
    )

@app.route("/mode_select")
def mode_select():
    user_id = request.args.get("user_id")
    username = request.args.get("username")
    return render_template("mode_select.html", user_id=user_id, username=username)


@app.route("/start_solo_game")
def start_solo_game():
    user_id = request.args.get("user_id")

    if not user_id:
        return "Missing user_id", 400

    with engine.begin() as conn:
        # Get next available Game_id
        game_id = conn.execute(text("""
            SELECT COALESCE(MAX(Game_id), 0) + 1 AS new_game_id FROM Games
        """)).scalar()

        time_limit = 10  # You can change this if needed

        # Insert new game with solo settings
        conn.execute(text("""
            INSERT INTO Games (Game_id, Time_limit_minutes, Finished, Num_players)
            VALUES (:game_id, :time_limit, FALSE, 1)
        """), {"game_id": game_id, "time_limit": time_limit})

        # Register the player
        conn.execute(text("""
            INSERT INTO Plays (User_id, Game_id, Hints_taken)
            VALUES (:user_id, :game_id, 0)
        """), {"user_id": user_id, "game_id": game_id})

    # Redirect to gameplay (where player will pick start/end)
    return redirect(url_for("gameplay", game_id=game_id, user_id=user_id))




@app.route("/start_guest_game")
def start_guest_game():
    import random
    import string

    # Generate a guest username
    random_suffix = ''.join(random.choices(string.digits, k=5))
    guest_username = f"Guest_{random_suffix}"

    # Get a new user ID by incrementing the current max
    result = g.conn.execute(text("SELECT MAX(User_id) AS max_id FROM Users")).mappings()
    max_id = result.fetchone()["max_id"]

    new_user_id = (max_id or 0) + 1

    # Insert the guest user
    insert_query = text("""
        INSERT INTO Users (User_id, Username, Password, Lobby_id, Experience_level, is_guest)
        VALUES (:user_id, :username, '', NULL, 0, TRUE)
    """)
    g.conn.execute(insert_query, {
        "user_id": new_user_id,
        "username": guest_username
    })
    g.conn.commit()

    # Redirect to mode selection
    return redirect(url_for('mode_select', user_id=new_user_id, username=guest_username))



@app.route("/submit_account_creation", methods=["POST"])
def submit_account_creation():
    username = request.form["username"].strip()
    password = request.form["password"].strip()

    with engine.begin() as conn:
        # Check for case-insensitive username match
        existing = conn.execute(text("""
            SELECT * FROM Users WHERE LOWER(Username) = LOWER(:username)
        """), {"username": username}).fetchone()

        if existing:
            print(f"[DEBUG] Username '{username}' already exists")
            return render_template("create_account.html", error="Username already taken")

        # Get next user ID
        next_id = conn.execute(text("""
            SELECT COALESCE(MAX(User_id), 0) + 1 FROM Users
        """)).scalar()
        print(f"[DEBUG] Creating user ID {next_id} with username '{username}'")

        try:
            conn.execute(text("""
                INSERT INTO Users (User_id, Username, Password, Lobby_id, Experience_level)
                VALUES (:uid, :uname, :pwd, NULL, 0)
            """), {
                "uid": next_id,
                "uname": username,
                "pwd": password
            })
        except Exception as e:
            print(f"[ERROR] Failed to insert user: {e}")
            return render_template("create_account.html", error="Account creation failed")

        user_check = conn.execute(text("""
            SELECT * FROM Users WHERE User_id = :uid
        """), {"uid": next_id}).mappings().fetchone()

        print(f"[DEBUG] Inserted row: {user_check}")


    return redirect(url_for("login"))




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
        Run the server using:

            python server.py

        Show the help text using:

            python server.py --help
        """
        HOST, PORT = host, port
        print("running on %s:%d" % (HOST, PORT))
        
        # Use socketio.run to initialize the server with WebSocket support
        socketio.run(app, host=HOST, port=PORT, debug=debug)

    run()

