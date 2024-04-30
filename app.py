from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from scripts.lol_api_fetches import fetch_player_puuid, fetch_live_game, fetch_live_game_data, fetch_last_games, champions_id_to_name
import numpy as np
import pickle
import os
import json
import ast

# Import the API key from the environment variables
RIOT_API_KEY = os.getenv("RIOT_API_KEY")


app = Flask(__name__)

rfc = None
with open('pkl/rfc.pkl', 'rb') as file:
    rfc = pickle.load(file)

encoder_dict = {}
with open('pkl/encoder_dict.pkl', 'rb') as file:
    encoder_dict = pickle.load(file)

    
@app.route('/', methods=['GET', 'POST'])
def index():
    error_message = None
    games = None
    live_game = None

    if request.method == 'POST':
        if request.form.get('submit') == 'Last Matches':
            name = request.form.get('name')
            server = request.form.get('server')

            if not name or not server:
                error_message = 'Missing name or server parameter'
            else:
                player_puuid = fetch_player_puuid(name.split("#")[0], name.split("#")[1], RIOT_API_KEY)
                if player_puuid is None:
                    error_message = 'Failed to fetch player ID from Riot API'
                else:
                    games = fetch_last_games(player_puuid, server, RIOT_API_KEY)
                    if games is None:
                        error_message = 'Failed to fetch games from Riot API'
            return render_template('index.html', error_message=error_message, games=games, live_game=live_game, player_puuid=player_puuid, server=server, champions_id_to_name=champions_id_to_name)

        elif request.form.get('submit') == 'Live Game':
            name = request.form.get('name')
            server = request.form.get('server')

            if not name or not server:
                error_message = 'Missing name or server parameter'
            else:
                player_puuid = fetch_player_puuid(name.split("#")[0], name.split("#")[1], RIOT_API_KEY)
                if player_puuid is None:
                    error_message = 'Failed to fetch player ID from Riot API'
                
                live_game = fetch_live_game(player_puuid, server, RIOT_API_KEY)
                if live_game is None:
                    error_message = 'Failed to fetch live game from Riot API'
            return render_template('index.html', error_message=error_message, games=games, live_game=live_game, player_puuid=player_puuid, server=server, champions_id_to_name=champions_id_to_name)

    return render_template('index.html', error_message=error_message)

# Define a route for the prediction
@app.route('/predict', methods=['POST'])
def predict():
    # Get the input data for the game
    aux_dict = {"blue_champion_0": 0,
    "blue_champion_1": 0,
    "blue_champion_2": 0,
    "blue_champion_3": 0,
    "blue_champion_4": 0,
    "red_champion_0": 0,
    "red_champion_1": 0,
    "red_champion_2": 0,
    "red_champion_3": 0,
    "red_champion_4": 0,
    "blue_player_0_kd": 0,
    "blue_player_0_wr": 0,
    "blue_player_1_kd": 0,
    "blue_player_1_wr": 0,
    "blue_player_2_kd": 0,
    "blue_player_2_wr": 0,
    "blue_player_3_kd": 0,
    "blue_player_3_wr": 0,
    "blue_player_4_kd": 0,
    "blue_player_4_wr": 0,
    "red_player_0_kd": 0,
    "red_player_0_wr": 0,
    "red_player_1_kd": 0,
    "red_player_1_wr": 0,
    "red_player_2_kd": 0,
    "red_player_2_wr": 0,
    "red_player_3_kd": 0,
    "red_player_3_wr": 0,
    "red_player_4_kd": 0,
    "red_player_4_wr": 0}

    player_puuid = request.form.get("playerpuuid")
    server = request.form.get("server")
    live_game = fetch_live_game(player_puuid, server, RIOT_API_KEY)
    if live_game is None:
        error_message = 'Failed to fetch live game from Riot API'

    #Get the champions names of the game
    live_game_champions = fetch_live_game_data(player_puuid, server, RIOT_API_KEY)

    red_counter = 0
    blue_counter = 0

    for player in live_game_champions.keys():
        if live_game_champions[player][3] == "blue":
            aux_dict[f"blue_champion_{blue_counter}"] = encoder_dict["champions"].transform([live_game_champions[player][0]])[0]
            aux_dict[f"blue_player_{blue_counter}_kd"] = live_game_champions[player][1]
            aux_dict[f"blue_player_{blue_counter}_wr"] = live_game_champions[player][2]
            blue_counter += 1
        else:
            aux_dict[f"red_champion_{red_counter}"] = encoder_dict["champions"].transform([live_game_champions[player][0]])[0]
            aux_dict[f"red_player_{red_counter}_kd"] = live_game_champions[player][1]
            aux_dict[f"red_player_{red_counter}_wr"] = live_game_champions[player][2]
            red_counter += 1

    # # Make a prediction
    input_data = [
        aux_dict["blue_champion_0"],
        aux_dict["blue_champion_1"],
        aux_dict["blue_champion_2"],
        aux_dict["blue_champion_3"],
        aux_dict["blue_champion_4"],
        aux_dict["red_champion_0"],
        aux_dict["red_champion_1"],
        aux_dict["red_champion_2"],
        aux_dict["red_champion_3"],
        aux_dict["red_champion_4"],
        aux_dict["blue_player_0_kd"],
        aux_dict["blue_player_0_wr"],
        aux_dict["blue_player_1_kd"],
        aux_dict["blue_player_1_wr"],
        aux_dict["blue_player_2_kd"],
        aux_dict["blue_player_2_wr"],
        aux_dict["blue_player_3_kd"],
        aux_dict["blue_player_3_wr"],
        aux_dict["blue_player_4_kd"],
        aux_dict["blue_player_4_wr"],
        aux_dict["red_player_0_kd"],
        aux_dict["red_player_0_wr"],
        aux_dict["red_player_1_kd"],
        aux_dict["red_player_1_wr"],
        aux_dict["red_player_2_kd"],
        aux_dict["red_player_2_wr"],
        aux_dict["red_player_3_kd"],
        aux_dict["red_player_3_wr"],
        aux_dict["red_player_4_kd"],
        aux_dict["red_player_4_wr"]
    ]
    input_data = np.array(input_data).reshape(1, -1)
    
    prob_prediction = rfc.predict_proba(input_data)
    prediction = rfc.predict(input_data)

    winner = encoder_dict["current_game_winner"].inverse_transform(prediction)[0]
    prob = prob_prediction[0][prediction[0]]
    return render_template('index.html', live_game=live_game, winner=winner, input_data=aux_dict, probabilidad=prob, error_message=error_message, champions_id_to_name=champions_id_to_name)

if __name__ == '__main__':
    app.run(debug=True)
