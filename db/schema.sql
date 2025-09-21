{\rtf1\ansi\ansicpg1252\cocoartf2821
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fmodern\fcharset0 Courier;}
{\colortbl;\red255\green255\blue255;\red15\green112\blue1;\red255\green255\blue255;\red0\green0\blue0;
\red0\green0\blue255;\red19\green118\blue70;\red100\green117\blue135;}
{\*\expandedcolortbl;;\cssrgb\c0\c50196\c0;\cssrgb\c100000\c100000\c100000;\cssrgb\c0\c0\c0;
\cssrgb\c0\c0\c100000;\cssrgb\c3529\c52549\c34510;\cssrgb\c46667\c53333\c60000;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\deftab720
\pard\pardeftab720\partightenfactor0

\f0\fs28 \cf2 \cb3 \expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 #Add all table schemas\cf0 \cb1 \strokec4 \
\
\pard\pardeftab720\partightenfactor0
\cf5 \cb3 \strokec5 %%sql\cf0 \cb1 \strokec4 \
\
\cf5 \cb3 \strokec5 DROP TABLE IF EXISTS\cf0 \strokec4  Chains;\cb1 \
\cf5 \cb3 \strokec5 DROP TABLE IF EXISTS\cf0 \strokec4  Acts_In_Connections;\cb1 \
\cf5 \cb3 \strokec5 DROP TABLE IF EXISTS\cf0 \strokec4  Movies;\cb1 \
\cf5 \cb3 \strokec5 DROP TABLE IF EXISTS\cf0 \strokec4  Plays;\cb1 \
\cf5 \cb3 \strokec5 DROP TABLE IF EXISTS\cf0 \strokec4  Games;\cb1 \
\cf5 \cb3 \strokec5 DROP TABLE IF EXISTS\cf0 \strokec4  Actors;\cb1 \
\cf5 \cb3 \strokec5 DROP TABLE IF EXISTS\cf0 \strokec4  Users;\cb1 \
\cf5 \cb3 \strokec5 DROP TABLE IF EXISTS\cf0 \strokec4  Lobbies;\cb1 \
\
\cf5 \cb3 \strokec5 CREATE TABLE\cf0 \strokec4  Lobbies (\cb1 \
\pard\pardeftab720\partightenfactor0
\cf0 \cb3     Lobby_id INT \cf5 \strokec5 PRIMARY\cf0 \strokec4  \cf5 \strokec5 KEY\cf0 \strokec4 ,\cb1 \
\cb3     Lobby_Name TEXT,\cb1 \
\cb3     Min_experience_level INT,\cb1 \
\cb3     Time_limit_minutes INT\cb1 \
\cb3 );\cb1 \
\
\pard\pardeftab720\partightenfactor0
\cf5 \cb3 \strokec5 CREATE TABLE\cf0 \strokec4  Users (\cb1 \
\pard\pardeftab720\partightenfactor0
\cf0 \cb3     User_id INT \cf5 \strokec5 PRIMARY\cf0 \strokec4  \cf5 \strokec5 KEY\cf0 \strokec4 ,\cb1 \
\cb3     Username TEXT,\cb1 \
\cb3     Password TEXT,\cb1 \
\cb3     Lobby_id INT,\cb1 \
\cb3     Experience_level INT,\cb1 \
\cb3     \cf5 \strokec5 FOREIGN\cf0 \strokec4  \cf5 \strokec5 KEY\cf0 \strokec4  (Lobby_id) \cf5 \strokec5 REFERENCES\cf0 \strokec4  Lobbies (Lobby_id) \cf5 \strokec5 ON\cf0 \strokec4  \cf5 \strokec5 DELETE\cf0 \strokec4  \cf5 \strokec5 SET\cf0 \strokec4  \cf5 \strokec5 NULL\cf0 \cb1 \strokec4 \
\cb3 );\cb1 \
\
\pard\pardeftab720\partightenfactor0
\cf5 \cb3 \strokec5 CREATE TABLE\cf0 \strokec4  Actors (\cb1 \
\pard\pardeftab720\partightenfactor0
\cf0 \cb3     Actor_id INT \cf5 \strokec5 PRIMARY\cf0 \strokec4  \cf5 \strokec5 KEY\cf0 \strokec4 ,\cb1 \
\cb3     \cf5 \strokec5 Name\cf0 \strokec4  TEXT,\cb1 \
\cb3     Birthdate DATE,\cb1 \
\cb3     Picture TEXT,  \cf2 \strokec2 -- URL\cf0 \cb1 \strokec4 \
\cb3     Weighted_centrality INT\cb1 \
\cb3 );\cb1 \
\
\pard\pardeftab720\partightenfactor0
\cf5 \cb3 \strokec5 CREATE TABLE\cf0 \strokec4  Games (\cb1 \
\pard\pardeftab720\partightenfactor0
\cf0 \cb3     Game_id INT \cf5 \strokec5 PRIMARY\cf0 \strokec4  \cf5 \strokec5 KEY\cf0 \strokec4 ,\cb1 \
\cb3     Time_limit_minutes INT,\cb1 \
\cb3     Start_point INT,\cb1 \
\cb3     End_point INT,\cb1 \
\cb3     Finished BOOLEAN, \cf2 \strokec2 -- New\cf0 \cb1 \strokec4 \
\cb3     \cf5 \strokec5 FOREIGN\cf0 \strokec4  \cf5 \strokec5 KEY\cf0 \strokec4  (Start_point) \cf5 \strokec5 REFERENCES\cf0 \strokec4  Actors (Actor_id) \cf5 \strokec5 ON\cf0 \strokec4  \cf5 \strokec5 DELETE\cf0 \strokec4  \cf5 \strokec5 RESTRICT\cf0 \strokec4 ,\cb1 \
\cb3     \cf5 \strokec5 FOREIGN\cf0 \strokec4  \cf5 \strokec5 KEY\cf0 \strokec4  (End_point) \cf5 \strokec5 REFERENCES\cf0 \strokec4  Actors (Actor_id) \cf5 \strokec5 ON\cf0 \strokec4  \cf5 \strokec5 DELETE\cf0 \strokec4  \cf5 \strokec5 RESTRICT\cf0 \strokec4 ,\cb1 \
\cb3     Num_players INT \cf5 \strokec5 DEFAULT\cf0 \strokec4  \cf6 \strokec6 2\cf0 \strokec4 ,\cb1 \
\cb3     \cf5 \strokec5 CHECK\cf0 \strokec4  (Start_point \cf7 \strokec7 <>\cf0 \strokec4  End_point)  \cf2 \strokec2 -- New: Ensures start and end points are not the same\cf0 \cb1 \strokec4 \
\cb3 );\cb1 \
\
\pard\pardeftab720\partightenfactor0
\cf5 \cb3 \strokec5 CREATE TABLE\cf0 \strokec4  Plays (\cb1 \
\pard\pardeftab720\partightenfactor0
\cf0 \cb3     User_id INT,\cb1 \
\cb3     Game_id INT,\cb1 \
\cb3     Hints_taken INT,\cb1 \
\cb3     \cf5 \strokec5 PRIMARY\cf0 \strokec4  \cf5 \strokec5 KEY\cf0 \strokec4  (User_id, Game_id),\cb1 \
\cb3     \cf5 \strokec5 FOREIGN\cf0 \strokec4  \cf5 \strokec5 KEY\cf0 \strokec4  (User_id) \cf5 \strokec5 REFERENCES\cf0 \strokec4  Users (User_id) \cf5 \strokec5 ON\cf0 \strokec4  \cf5 \strokec5 DELETE\cf0 \strokec4  \cf5 \strokec5 CASCADE\cf0 \strokec4 ,\cb1 \
\cb3     \cf5 \strokec5 FOREIGN\cf0 \strokec4  \cf5 \strokec5 KEY\cf0 \strokec4  (Game_id) \cf5 \strokec5 REFERENCES\cf0 \strokec4  Games (Game_id) \cf5 \strokec5 ON\cf0 \strokec4  \cf5 \strokec5 DELETE\cf0 \strokec4  \cf5 \strokec5 CASCADE\cf0 \cb1 \strokec4 \
\cb3 );\cb1 \
\
\pard\pardeftab720\partightenfactor0
\cf5 \cb3 \strokec5 CREATE TABLE\cf0 \strokec4  Movies (\cb1 \
\pard\pardeftab720\partightenfactor0
\cf0 \cb3     Movie_id INT \cf5 \strokec5 PRIMARY\cf0 \strokec4  \cf5 \strokec5 KEY\cf0 \strokec4 ,\cb1 \
\cb3     Title TEXT,\cb1 \
\cb3     Release DATE,\cb1 \
\cb3     Poster TEXT,  \cf2 \strokec2 -- URL\cf0 \cb1 \strokec4 \
\cb3     IMDB_vote_count INT\cb1 \
\cb3 );\cb1 \
\
\
\pard\pardeftab720\partightenfactor0
\cf5 \cb3 \strokec5 CREATE TABLE\cf0 \strokec4  Acts_In_Connections (\cb1 \
\pard\pardeftab720\partightenfactor0
\cf0 \cb3     Connection_id INT \cf5 \strokec5 PRIMARY\cf0 \strokec4  \cf5 \strokec5 KEY\cf0 \strokec4 ,\cb1 \
\cb3     Actor_id INT,\cb1 \
\cb3     Movie_id INT,\cb1 \
\cb3     \cf5 \strokec5 FOREIGN\cf0 \strokec4  \cf5 \strokec5 KEY\cf0 \strokec4  (Actor_id) \cf5 \strokec5 REFERENCES\cf0 \strokec4  Actors (Actor_id) \cf5 \strokec5 ON\cf0 \strokec4  \cf5 \strokec5 DELETE\cf0 \strokec4  \cf5 \strokec5 CASCADE\cf0 \strokec4 ,\cb1 \
\cb3     \cf5 \strokec5 FOREIGN\cf0 \strokec4  \cf5 \strokec5 KEY\cf0 \strokec4  (Movie_id) \cf5 \strokec5 REFERENCES\cf0 \strokec4  Movies (Movie_id) \cf5 \strokec5 ON\cf0 \strokec4  \cf5 \strokec5 DELETE\cf0 \strokec4  \cf5 \strokec5 CASCADE\cf0 \strokec4 ,\cb1 \
\cb3     \cf5 \strokec5 UNIQUE\cf0 \strokec4  (Actor_id, Movie_id)\cb1 \
\cb3 );\cb1 \
\
\pard\pardeftab720\partightenfactor0
\cf5 \cb3 \strokec5 CREATE TABLE\cf0 \strokec4  Chains (\cb1 \
\pard\pardeftab720\partightenfactor0
\cf0 \cb3     Connection_id INT,\cb1 \
\cb3     Game_id INT,\cb1 \
\cb3     User_id INT,\cb1 \
\cb3     Move_number INT,\cb1 \
\cb3     \cf5 \strokec5 PRIMARY\cf0 \strokec4  \cf5 \strokec5 KEY\cf0 \strokec4  (Connection_id, Game_id, User_id),\cb1 \
\cb3     \cf5 \strokec5 FOREIGN\cf0 \strokec4  \cf5 \strokec5 KEY\cf0 \strokec4  (Connection_id) \cf5 \strokec5 REFERENCES\cf0 \strokec4  Acts_In_Connections (Connection_id) \cf5 \strokec5 ON\cf0 \strokec4  \cf5 \strokec5 DELETE\cf0 \strokec4  \cf5 \strokec5 CASCADE\cf0 \strokec4 ,\cb1 \
\cb3     \cf5 \strokec5 FOREIGN\cf0 \strokec4  \cf5 \strokec5 KEY\cf0 \strokec4  (Game_id) \cf5 \strokec5 REFERENCES\cf0 \strokec4  Games (Game_id) \cf5 \strokec5 ON\cf0 \strokec4  \cf5 \strokec5 DELETE\cf0 \strokec4  \cf5 \strokec5 SET\cf0 \strokec4  \cf5 \strokec5 NULL\cf0 \strokec4 ,\cb1 \
\cb3     \cf5 \strokec5 FOREIGN\cf0 \strokec4  \cf5 \strokec5 KEY\cf0 \strokec4  (User_id) \cf5 \strokec5 REFERENCES\cf0 \strokec4  Users (User_id) \cf5 \strokec5 ON\cf0 \strokec4  \cf5 \strokec5 DELETE\cf0 \strokec4  \cf5 \strokec5 CASCADE\cf0 \strokec4 ,\cb1 \
\cb3     \cf5 \strokec5 UNIQUE\cf0 \strokec4  (Game_id, Move_number),\cb1 \
\cb3     \cf5 \strokec5 UNIQUE\cf0 \strokec4  (Connection_id, Game_id)\cb1 \
\cb3 );\cb1 \
\
}