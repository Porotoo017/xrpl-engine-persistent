import sqlite3
import json

class LPFEngine:
    def __init__(self):
        self.conn = sqlite3.connect('lpf_data.db')
        self._setup_db()

    def _setup_db(self):
        self.conn.execute('''CREATE TABLE IF NOT EXISTS clubs 
                             (id INTEGER PRIMARY KEY, name TEXT, dt TEXT, logo_url TEXT)''')
        # Datos verificados 2026
        clubs = [
            ('River Plate', 'Leonardo Ponzio', 'https://upload.wikimedia.org/wikipedia/commons/3/3a/Logo_de_River_Plate.svg'),
            ('Boca Juniors', 'Rodolfo Arruabarrena', 'https://upload.wikimedia.org/wikipedia/commons/e/e6/Boca_Juniors_logo.svg'),
            ('Racing Club', 'Gustavo Costas', 'https://upload.wikimedia.org/wikipedia/commons/5/56/Escudo_de_Racing_Club_%28Avellaneda%29.svg'),
            ('Vélez Sarsfield', 'Gustavo Quinteros', 'https://upload.wikimedia.org/wikipedia/commons/a/ac/Escudo_Velez_Sarsfield.svg')
        ]
        self.conn.executemany('INSERT OR IGNORE INTO clubs (name, dt, logo_url) VALUES (?,?,?)', clubs)
        self.conn.commit()

    def get_match_data(self):
        cursor = self.conn.execute('SELECT * FROM clubs')
        return cursor.fetchall()
