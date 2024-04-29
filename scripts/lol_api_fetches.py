import requests
import pandas as pd

champions_name_to_id = pd.read_json("champions.json")["name_to_id"]
champions_id_to_name = {}
for key, value in champions_name_to_id.items():
    champions_id_to_name[value] = key

def fetch_player_puuid(player, tag, RIOT_API_KEY):
    url = f'https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{player}/{tag}?api_key={RIOT_API_KEY}'
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch player ID for {player} from Riot API. Error: {e}")
        return None

    if response.status_code == 200:
        return response.json()['puuid']
    else:
        print(f"Failed to fetch player ID for {player} from Riot API. Status code: {response.status_code}")
        return None

def fetch_live_game(player_puuid, server, RIOT_API_KEY):
    url = f"https://{server}.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{player_puuid}?api_key={RIOT_API_KEY}"
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch live game for player {player_puuid} from Riot API. Error: {e}")
        return None

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        msg = "The player is not in a current match."
        return msg
    else:
        print(f"Failed to fetch live game for player {player_puuid} from Riot API. Status code: {response.status_code}")
        return None
    
def fetch_last_games(player_puuid, server, RIOT_API_KEY):
    region = "americas" if server in ["na1", "la1", "la2", "br1"] else "europe"
    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{player_puuid}/ids?start=0&count=20&api_key={RIOT_API_KEY}"
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch last games for player {player_puuid} from Riot API. Error: {e}")
        return None
    games = []
    if response.status_code == 200:
        for game_id in response.json():
            url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{game_id}?api_key={RIOT_API_KEY}"
            try:
                game_response = requests.get(url)
            except requests.exceptions.RequestException as e:
                print(f"Failed to fetch game {game_id} for player {player_puuid} from Riot API. Error: {e}")
                continue
            if game_response.status_code == 200:
                participants = game_response.json()['info']['participants']
                players_champions = {participant['puuid']: participant['championName'] for participant in participants}
                winner = "Team 1" if game_response.json()['info']['teams'][0]['win'] else "Team 2"
                games.append([players_champions, winner])
            else:
                print(f"Failed to fetch game {game_id} for player {player_puuid} from Riot API. Status code: {game_response.status_code}")
        return games
    else:
        print(f"Failed to fetch last games for player {player_puuid} from Riot API. Status code: {response.status_code}")
        return None
    
def fetch_live_game_data(player_puuid, server, RIOT_API_KEY):
    region = "americas" if server in ["NA1", "LA1", "LA2", "BR1"] else "europe"
    url = f"https://{server}.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{player_puuid}?api_key={RIOT_API_KEY}"
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch live game for player {player_puuid} from Riot API. Error: {e}")
        return None
    if response.status_code == 200:
        #log the response
        participants = response.json()['participants']
        red_players = [participant['puuid'] for participant in participants if participant['teamId'] == 200]
        blue_players = [participant['puuid'] for participant in participants if participant['teamId'] == 100]
        players_champions = {participant['puuid']: participant['championId'] for participant in participants}
        # Get the winrate and kills/death over the last 5 games of each player in the game
        for player in players_champions.keys():
            player_url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{player}/ids?start=0&count=5&api_key={RIOT_API_KEY}"
            try:
                player_response = requests.get(player_url)
            except requests.exceptions.RequestException as e:
                print(f"Failed to fetch last games for player {player} from Riot API. Error: {e}")
                continue
            if player_response.status_code == 200:
                player_games = player_response.json()
                print(f"Player {player} has played the following games: {player_games}")
                player_kills = 0
                player_deaths = 0
                player_wr = 0
                for player_game in player_games:
                    player_game_url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{player_game}?api_key={RIOT_API_KEY}"
                    try:
                        player_game_response = requests.get(player_game_url)
                    except requests.exceptions.RequestException as e:
                        print(f"Failed to fetch game {player_game} for player {player} from Riot API. Error: {e}")
                        continue
                    if player_game_response.status_code == 200:
                        player_game_info = player_game_response.json()['info']
                        for player_info in player_game_info['participants']:
                            if player_info['puuid'] == player:
                                player_kills += player_info['kills']
                                player_deaths += player_info['deaths']
                                player_wr += 1 if player_info['win'] else 0
                                break
                    else:
                        print(f"Failed to fetch game {player_game} for player {player} from Riot API. Status code: {player_game_response.status_code}")
                player_kd = player_kills / max(1, player_deaths)
                player_wr /= max(1, len(player_games))
                players_champions[player] = [champions_id_to_name[players_champions[player]], player_kd, player_wr, "blue" if player in blue_players else "red"]
            else:
                print(f"Failed to fetch last games for player {player} from Riot API. Status code: {player_response.status_code}")
        
            
        #Returns a dictionary with the puuid of the player as the key and the champion name, player_kd, player_wr, team as the value
        return players_champions
    else:
        print(f"Failed to fetch game {player_puuid} from Riot API. Status code: {response.status_code}")
        return None
