
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
from flask import Flask, request, render_template, g, redirect, Response, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
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

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Socket disconnected for User ID: {request.args.get('user_id')}")


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
    user_id = request.args.get('user_id')
    message = request.args.get('message')  # These will be None if not passed
    message_lobby_id = request.args.get('message_lobby_id')
    username = request.args.get('username')

    
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




@socketio.on("join_lobby")
def handle_join_lobby(data):
    lobby_id = data["lobby_id"]
    user_id = data["user_id"]
    room_name = f"lobby_{lobby_id}"

    join_room(room_name)
    print(f"User {user_id} joined lobby {lobby_id}")
    
    # Use `engine.connect()` for database operations
    with engine.connect() as connection:
        trans = connection.begin()  # Start a transaction here
        
        try:
            room_members = list(socketio.server.manager.get_participants("/", room_name))
            print(f"Current participants in {room_name}: {room_members}")

            # Update user's lobby_id
            update_user_lobby = text("""
                UPDATE Users SET Lobby_id = :lobby_id WHERE User_id = :user_id
            """)
            connection.execute(update_user_lobby, {"lobby_id": lobby_id, "user_id": user_id})
            
            if len(room_members) == 2:
                game_id = create_game(connection, lobby_id, trans)  # Pass the transaction
                other_user_id = get_other_user_in_room(connection, lobby_id, user_id)
                if other_user_id is None:
                    raise ValueError(f"Could not find other user in lobby {lobby_id}")
                add_players_to_game(connection, game_id, user_id, other_user_id, trans)  # Pass the transaction
                # Emit the start_game event with additional information
                # After create_game and add_players_to_game in join_lobby route
                socketio.emit(
                    "start_game",
                    {"game_id": game_id, "user1_id": user_id, "user2_id": other_user_id},
                    room=f"lobby_{lobby_id}"
                )
            else:
                emit("waiting", {"message": "Waiting for another player"}, room=room_name)

            trans.commit()  # Commit all changes once complete
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
    lobby_id = request.args.get("lobby_id")  # You can also get lobby_id from `data` if needed
    print(f"User {user_id} left lobby {lobby_id}.")

    # Perform additional cleanup or leave the room
    if lobby_id:
        try:
            leave_room(f"lobby_{lobby_id}")
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

    if not game:
        return "Game not found", 404

    # Fetch players and determine roles
    players_query = text("SELECT user_id FROM Plays WHERE game_id = :game_id ORDER BY user_id")
    players = g.conn.execute(players_query, {"game_id": game_id}).mappings().fetchall()

    if len(players) < 2:
        return "Players not properly initialized", 400

    start_setter = players[0]["user_id"]
    end_setter = players[1]["user_id"]

    # Logic for determining next action
    if int(user_id) == start_setter:
        if not game["start_point"]:
            next_action = "start_point"  # Set start point
        elif not game["end_point"]:
            next_action = "play_game"  # Waiting for end-setter
        else:
            next_action = "play_game"  # Game starts
    elif int(user_id) == end_setter:
        if not game["end_point"]:
            next_action = "end_point"  # Set end point
        elif game["start_point"]:
            next_action = "play_game"  # Waiting for gameplay
        else:
            next_action = "play_game"  # Game starts
    else:
        return "Invalid user", 400

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




@app.route("/set_start_point/<int:game_id>", methods=["POST"])
def set_start_point(game_id):
    user_id = request.args.get("user_id")
    actor_name = request.form["actor_name"]

    with engine.connect() as connection:
        actor_query = text("SELECT actor_id FROM Actors WHERE name = :actor_name")
        actor = connection.execute(actor_query, {"actor_name": actor_name}).mappings().fetchone()

        if actor:
            update_game_query = text("UPDATE Games SET start_point = :actor_id WHERE game_id = :game_id")
            connection.execute(update_game_query, {"actor_id": actor["actor_id"], "game_id": game_id})
            connection.commit()

            # Determine the next action
            game_query = text("SELECT * FROM Games WHERE game_id = :game_id")
            game = connection.execute(game_query, {"game_id": game_id}).mappings().fetchone()
            if game["end_point"]:
                next_action = "play_game"
            else:
                next_action = "end_point"
                
            # Process player readiness
            ready_count = process_player_ready(game_id, user_id)

            # If both players are ready, skip re-rendering gameplay
            if ready_count == 2:
                print(f"Redirecting to /game_stage/{game_id}?user_id={user_id}&start_point={game['start_point']}&end_point={game['end_point']}")
                return redirect(f"/game_stage/{game_id}?user_id={user_id}&start_point={game['start_point']}&end_point={game['end_point']}")
            else:
                #return "", 204  # Client dynamically updates UI
                    # Redirect back to gameplay with updated next_action
                return redirect(f"/gameplay/{game_id}?user_id={user_id}&next_action={next_action}")
        else:
            return "Actor not found", 400



@app.route("/set_end_point/<int:game_id>", methods=["POST"])
def set_end_point(game_id):
    user_id = request.args.get("user_id")
    actor_name = request.form["actor_name"]

    with engine.connect() as connection:
        actor_query = text("SELECT actor_id FROM Actors WHERE name = :actor_name")
        actor = connection.execute(actor_query, {"actor_name": actor_name}).mappings().fetchone()

        if actor:
            update_game_query = text("UPDATE Games SET end_point = :actor_id WHERE game_id = :game_id")
            connection.execute(update_game_query, {"actor_id": actor["actor_id"], "game_id": game_id})
            connection.commit()

            # Determine the next action
            game_query = text("SELECT * FROM Games WHERE game_id = :game_id")
            game = connection.execute(game_query, {"game_id": game_id}).mappings().fetchone()
            if game["start_point"]:
                next_action = "play_game"
            else:
                next_action = "start_point"
                
            
            # Process player readiness
            ready_count = process_player_ready(game_id, user_id)

            # If both players are ready, skip re-rendering gameplay
            if ready_count == 2:
                print(f"Redirecting to /game_stage/{game_id}?user_id={user_id}&start_point={game['start_point']}&end_point={game['end_point']}")
                return redirect(f"/game_stage/{game_id}?user_id={user_id}&start_point={game['start_point']}&end_point={game['end_point']}")
            else:
                #return "", 204  # Client dynamically updates UI
                    # Redirect back to gameplay with updated next_action
                return redirect(f"/gameplay/{game_id}?user_id={user_id}&next_action={next_action}")
        else:
            return "Actor not found", 400




@socketio.on("start_game")
def handle_start_game(data):
    lobby_id = data["lobby_id"]
    game_id = data["game_id"]

    # Emit to all players in the room that the game has started
    emit("game_started", {"game_id": game_id}, room=f"lobby_{lobby_id}")
    print(f"Game {game_id} started for lobby {lobby_id}")

# Track readiness in-memory (consider using a database for persistence in production)
ready_players = {}

def process_player_ready(game_id, user_id):
    global ready_players

    # Initialize the ready_players entry for this game if it doesn't exist
    if game_id not in ready_players:
        ready_players[game_id] = set()

    # Add the current player to the set of ready players
    ready_players[game_id].add(user_id)
    print(f"Player {user_id} is ready for game {game_id}. Ready players: {ready_players[game_id]}")

    # Debugging: Print the length of ready players
    print(f"Number of ready players for game {game_id}: {len(ready_players[game_id])}")

    # Check if both players are ready
    if len(ready_players[game_id]) == 2:
        print(f"Both players are ready for game {game_id}. Emitting start_game.")

        # Use a direct connection to fetch game details
        with engine.connect() as connection:
            game_query = text("SELECT * FROM Games WHERE game_id = :game_id")
            game = connection.execute(game_query, {"game_id": game_id}).mappings().fetchone()

            if not game or not game["start_point"] or not game["end_point"]:
                print(f"Error: Missing start_point or end_point for game {game_id}.")
                return
                
            print(f"Room members for game_{game_id}:")
            if game_room_members := socketio.server.manager.rooms.get(f"game_{game_id}"):
                for sid in game_room_members:
                    print(f"- Session ID: {sid}")
            else:
                print(f"No members found in room: game_{game_id}")


            # Emit start_game to individual player rooms
            # Iterate through the set of user_ids for the specific game_id
            for player_id in ready_players[game_id]:
                if player_id!=user_id:
                    room_name = f"game_{game_id}_player_{player_id}"
                    print(f"Emitting start_game to room: {room_name} for User ID: {player_id}")
                    socketio.sleep(1)  # Add a slight delay
                    # Emit the start_game event to the player's individual room
                    socketio.emit(
                        "start_game",
                        {
                            "game_id": game_id,
                            "user_id": player_id,  # Send the user ID specific to the player
                            "start_point": game["start_point"],
                            "end_point": game["end_point"]
                        },
                        room=room_name
                    )
                    print(f"Start_game emitted to room: {room_name}, for user_id: {player_id}")

            print(f"Current rooms for game {game_id}: {socketio.server.rooms}")
            return 2

    else:
        print(f"Waiting for more players to be ready for game {game_id}.")
        return len(ready_players[game_id])


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

    if not game:
        return "Game not found", 404

    # Fetch the start and end points
    start_actor_query = text("SELECT name FROM Actors WHERE actor_id = :actor_id")
    start_actor = g.conn.execute(start_actor_query, {"actor_id": game["start_point"]}).mappings().fetchone()["name"]

    end_actor_query = text("SELECT name FROM Actors WHERE actor_id = :actor_id")
    end_actor = g.conn.execute(end_actor_query, {"actor_id": game["end_point"]}).mappings().fetchone()["name"]

    # Fetch game players
    players_query = text("SELECT user_id FROM Plays WHERE game_id = :game_id")
    players = g.conn.execute(players_query, {"game_id": game_id}).mappings().fetchall()
    if len(players) != 2:
        return "Invalid number of players in the game", 400

    user1_id, user2_id = players[0]["user_id"], players[1]["user_id"]

    # Determine the current player's turn based on the last move
    last_move_query = text("""
        SELECT user_id, move_number FROM Chains
        WHERE game_id = :game_id
        ORDER BY move_number DESC LIMIT 1
    """)
    last_move = g.conn.execute(last_move_query, {"game_id": game_id}).mappings().fetchone()

    if last_move:
        # Alternate between the two players
        player_turn = user1_id if last_move["user_id"] == user2_id else user2_id
        turn_number = last_move["move_number"] + 1
    else:
        # Start with user1 if no moves exist
        player_turn = user1_id
        turn_number = 0  # First move

    # Determine move_type based on turn_number
    move_type = "movie" if turn_number % 2 == 0 else "actor"

    print(f"Debug: user1_id={user1_id}, user2_id={user2_id}")
    print(f"Debug: last_move={last_move}")
    print(f"Debug: Calculated player_turn={player_turn}, current user_id={user_id}")
    print(f"Debug: move_type={move_type}, turn_number={turn_number}")
    print(f"Debug: Rendering game_stage with start_actor={start_actor}, end_actor={end_actor}, user_id={user_id}, player_turn={player_turn}")

    # Render the game_stage template
    return render_template(
        "game_stage.html",
        game=game,
        start_actor=start_actor,
        end_actor=end_actor,
        user_id=user_id,
        player_turn=player_turn,
        move_type=move_type,
        last_move_id=game["start_point"]  # Initialize with start_point for the first render
    )



@socketio.on("make_move")
def handle_make_move(data):
    user_id = data.get("user_id")
    game_id = data.get("game_id")
    move = data.get("move")
    move_type = data.get("move_type")
    last_move_id = data.get("last_move_id")

    print(f"Received move from user {user_id} for game {game_id}: {move}, move_type: {move_type}, last_move_id: {last_move_id}")

    # Use an explicit connection to handle database operations
    with engine.connect() as connection:
        # Determine the move's ID based on the type (actor or movie)
        if move_type == "actor":
            move_query = text("SELECT actor_id FROM Actors WHERE name = :move_name")
        elif move_type == "movie":
            move_query = text("SELECT movie_id FROM Movies WHERE title = :move_name")
        else:
            print("Invalid move type.")
            socketio.emit("game_error", {"message": "Invalid move type."}, room=f"game_{game_id}_player_{user_id}")
            return
        
        move_result = connection.execute(move_query, {"move_name": move}).mappings().fetchone()
        if not move_result:
            print("Invalid move. Move not found in database.")
            socketio.emit("game_error", {"message": "Invalid move. Please try again."}, room=f"game_{game_id}_player_{user_id}")
            return
        
        current_move_id = move_result["actor_id"] if move_type == "actor" else move_result["movie_id"]

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
            socketio.emit("game_error", {"message": "Invalid connection. Please try again."}, room=f"game_{game_id}_player_{user_id}")
            return

        connection_id = connection_result["connection_id"]

        # Insert the move into the Chains table
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
        

        print("Move successfully recorded in Chains.")
        
        
        
        # Check if game is finished
        game_query = text("SELECT end_point FROM Games WHERE game_id = :game_id")
        game = connection.execute(game_query, {"game_id": game_id}).mappings().fetchone()
        if move_type == "actor" and current_move_id == game["end_point"]:
            print("Game over! End point reached.")
            
            # Update the Games table to mark the game as finished
            update_game_query = text("UPDATE Games SET Finished = TRUE WHERE game_id = :game_id")
            connection.execute(update_game_query, {"game_id": game_id})
            connection.commit()

            # Notify players that the game is over
            socketio.emit("game_over", {"game_id": game_id}, room=f"game_{game_id}")
            return
        
        # Log game_id before using it in the query
        print(f"Debug: game_id before query = {game_id}")

        # Fetch game players to determine the next turn
        players_query = text("SELECT user_id FROM Plays WHERE game_id = :game_id")
        players = connection.execute(players_query, {"game_id": game_id}).mappings().fetchall()
        if len(players) != 2:
            print("Invalid number of players in the game.")
            socketio.emit("game_error", {"message": "Game configuration error."}, room=f"game_{game_id}_player_{user_id}")
            return

        user1_id, user2_id = players[0]["user_id"], players[1]["user_id"]

        # Determine the next turn
        next_turn = user1_id if user_id == user2_id else user2_id

        # Determine the next move type
        next_move_type = "movie" if move_type == "actor" else "actor"

        # Include move_type in the game_update emission
        game_update = {
            "game_id": game_id,
            "move": move,
            "last_move_id": current_move_id,
            "next_turn": next_turn,
            "move_type": next_move_type  # Send the toggled move type
        }

        print(f"Emitting game_update: {game_update}")
        socketio.emit("game_update", game_update, room=f"game_{game_id}")







@socketio.on("connect")
def handle_gameplay_connect():
    user_id = request.args.get("user_id")
    game_id = request.args.get("game_id")
    if not user_id or not game_id:
        print("Missing user_id or game_id in gameplay socket connection.")
        return
        
    print(f"Connect event received: user_id={request.args.get('user_id')}, game_id={request.args.get('game_id')}")

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
    
    # Check if the user was in a game or a lobby and clean up
    if request.args.get("game_id"):
        print(f"User {user_id} disconnected from game.")
    else:
        print(f"User {user_id} disconnected from lobby.")




    
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
        username=username
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

