import requests
import os
import sqlite3
import json

class FootballEngine:
    def __init__(self, api_token):
        self.api_token = api_token
        self.headers = {'X-Auth-Token': self.api_token}
        self.base_url = "https://api.football-data.org/v4"
        self.db = "football_data.db"
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db)
        conn.execute("CREATE TABLE IF NOT EXISTS matches (id INTEGER PRIMARY KEY, league TEXT, home TEXT, away TEXT, status TEXT, result TEXT)")
        conn.commit()
        conn.close()

    def get_matches(self, league_code):
        url = f"{self.base_url}/competitions/{league_code}/matches"
        response = requests.get(url, headers=self.headers)
        return response.json()

# Configuración inicial del motor
if __name__ == "__main__":
    # Token provisto por football-data.org para Porotoo017
    TOKEN = "0f562725e1a24d83a158b479f649a756" 
    engine = FootballEngine(TOKEN)
    print("Motor de Futbol Inicializado. Probando conexión...")
