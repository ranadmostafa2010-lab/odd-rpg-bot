
# core/database.py - SQLite database (no external setup needed!)
database_content = '''import sqlite3
import json
import os
from datetime import datetime, timedelta
from threading import Lock

class Database:
    def __init__(self, db_path='odd_rpg.db'):
        self.db_path = db_path
        self.lock = Lock()
        self.init_database()
    
    def get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize all tables"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Players table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    phone TEXT PRIMARY KEY,
                    username TEXT,
                    points INTEGER DEFAULT 1000,
                    bank INTEGER DEFAULT 0,
                    bank_tier TEXT DEFAULT 'basic',
                    power INTEGER DEFAULT 10,
                    health INTEGER DEFAULT 100,
                    max_health INTEGER DEFAULT 100,
                    level INTEGER DEFAULT 1,
                    exp INTEGER DEFAULT 0,
                    pets TEXT DEFAULT '[]',
                    inventory TEXT DEFAULT '[]',
                    used_codes TEXT DEFAULT '[]',
                    active_effects TEXT DEFAULT '{}',
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    steals_success INTEGER DEFAULT 0,
                    steals_failed INTEGER DEFAULT 0,
                    enchantments INTEGER DEFAULT 0,
                    last_daily TEXT,
                    last_steal TEXT,
                    joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    banned INTEGER DEFAULT 0,
                    ban_reason TEXT,
                    message_id TEXT,
                    chat_state TEXT DEFAULT '{}'
                )
            ''')
            
            # Battles table for active battles
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS active_battles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_phone TEXT,
                    enemy_name TEXT,
                    enemy_emoji TEXT,
                    enemy_hp INTEGER,
                    enemy_max_hp INTEGER,
                    enemy_damage TEXT,
                    player_hp INTEGER,
                    turn INTEGER DEFAULT 1,
                    battle_log TEXT DEFAULT '[]',
                    reward INTEGER,
                    rarity TEXT,
                    started TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (player_phone) REFERENCES players(phone)
                )
            ''')
            
            # Boss battles
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS boss_battles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    boss_name TEXT,
                    boss_emoji TEXT,
                    boss_hp INTEGER,
                    boss_max_hp INTEGER,
                    participants TEXT DEFAULT '[]',
                    damage_dealt TEXT DEFAULT '{}',
                    status TEXT DEFAULT 'active',
                    spawned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ends TIMESTAMP
                )
            ''')
            
            # Trade offers
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_phone TEXT,
                    to_phone TEXT,
                    offer_points INTEGER DEFAULT 0,
                    offer_pets TEXT DEFAULT '[]',
                    request_points INTEGER DEFAULT 0,
                    request_pets TEXT DEFAULT '[]',
                    status TEXT DEFAULT 'pending',
                    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (from_phone) REFERENCES players(phone),
                    FOREIGN KEY (to_phone) REFERENCES players(phone)
                )
            ''')
            
            # Messages for inbox system
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_phone TEXT,
                    to_phone TEXT,
                    message TEXT,
                    type TEXT DEFAULT 'private',
                    read INTEGER DEFAULT 0,
                    sent TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (from_phone) REFERENCES players(phone),
                    FOREIGN KEY (to_phone) REFERENCES players(phone)
                )
            ''')
            
            # Admin logs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_phone TEXT,
                    action TEXT,
                    target_phone TEXT,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Global stats
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS global_stats (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✅ Database initialized successfully!")
    
    def get_player(self, phone):
        """Get player data or create new"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM players WHERE phone = ?', (phone,))
            row = cursor.fetchone()
            
            if not row:
                # Create new player
                cursor.execute('''
                    INSERT INTO players (phone, points, bank, pets, inventory, used_codes)
                    VALUES (?, 1000, 0, '[]', '[]', '[]')
                ''', (phone,))
                conn.commit()
                
                player = {
                    'phone': phone,
                    'username': None,
                    'points': 1000,
                    'bank': 0,
                    'bank_tier': 'basic',
                    'power': 10,
                    'health': 100,
                    'max_health': 100,
                    'level': 1,
                    'exp': 0,
                    'pets': [],
                    'inventory': [],
                    'used_codes': [],
                    'active_effects': {},
                    'wins': 0,
                    'losses': 0,
                    'steals_success': 0,
                    'steals_failed': 0,
                    'enchantments': 0,
                    'last_daily': None,
                    'last_steal': None,
                    'banned': 0,
                    'ban_reason': None,
                    'message_id': None,
                    'chat_state': {}
                }
            else:
                player = self._row_to_dict(row)
                # Update last active
                cursor.execute('UPDATE players SET last_active = CURRENT_TIMESTAMP WHERE phone = ?', (phone,))
                conn.commit()
            
            conn.close()
            return player
    
    def save_player(self, phone, player_data):
        """Save player data"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE players SET
                    username = ?,
                    points = ?,
                    bank = ?,
                    bank_tier = ?,
                    power = ?,
                    health = ?,
                    max_health = ?,
                    level = ?,
                    exp = ?,
                    pets = ?,
                    inventory = ?,
                    used_codes = ?,
                    active_effects = ?,
                    wins = ?,
                    losses = ?,
                    steals_success = ?,
                    steals_failed = ?,
                    enchantments = ?,
                    last_daily = ?,
                    last_steal = ?,
                    banned = ?,
                    ban_reason = ?,
                    message_id = ?,
                    chat_state = ?
                WHERE phone = ?
            ''', (
                player_data.get('username'),
                player_data['points'],
                player_data['bank'],
                player_data.get('bank_tier', 'basic'),
                player_data['power'],
                player_data['health'],
                player_data['max_health'],
                player_data.get('level', 1),
                player_data.get('exp', 0),
                json.dumps(player_data['pets']),
                json.dumps(player_data['inventory']),
                json.dumps(player_data['used_codes']),
                json.dumps(player_data.get('active_effects', {})),
                player_data['wins'],
                player_data['losses'],
                player_data['steals_success'],
                player_data['steals_failed'],
                player_data['enchantments'],
                player_data.get('last_daily'),
                player_data.get('last_steal'),
                player_data.get('banned', 0),
                player_data.get('ban_reason'),
                player_data.get('message_id'),
                json.dumps(player_data.get('chat_state', {})),
                phone
            ))
            
            conn.commit()
            conn.close()
            return True
    
    def get_all_players(self):
        """Get all players for leaderboard"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM players WHERE banned = 0 ORDER BY (points + bank) DESC')
            rows = cursor.fetchall()
            conn.close()
            return [self._row_to_dict(row) for row in rows]
    
    def get_leaderboard(self, limit=10):
        """Get top players"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT phone, username, points, bank, wins, (points + bank) as total
                FROM players WHERE banned = 0
                ORDER BY total DESC LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
    
    def create_battle(self, phone, enemy_data):
        """Create active battle"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO active_battles 
                (player_phone, enemy_name, enemy_emoji, enemy_hp, enemy_max_hp, enemy_damage, player_hp, reward, rarity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                phone,
                enemy_data['name'],
                enemy_data['emoji'],
                enemy_data['hp'],
                enemy_data['hp'],
                enemy_data['damage'],
                enemy_data['player_hp'],
                enemy_data['reward'],
                enemy_data['rarity']
            ))
            
            battle_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return battle_id
    
    def get_active_battle(self, phone):
        """Get player's active battle"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM active_battles WHERE player_phone = ?', (phone,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
    
    def update_battle(self, battle_id, updates):
        """Update battle data"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            fields = ', '.join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [battle_id]
            
            cursor.execute(f'UPDATE active_battles SET {fields} WHERE id = ?', values)
            conn.commit()
            conn.close()
    
    def delete_battle(self, battle_id):
        """Delete battle"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM active_battles WHERE id = ?', (battle_id,))
            conn.commit()
            conn.close()
    
    def send_message(self, from_phone, to_phone, message, msg_type='private'):
        """Send message to player's inbox"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO messages (from_phone, to_phone, message, type)
                VALUES (?, ?, ?, ?)
            ''', (from_phone, to_phone, message, msg_type))
            conn.commit()
            conn.close()
    
    def get_messages(self, phone, unread_only=False):
        """Get player messages"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if unread_only:
                cursor.execute('SELECT * FROM messages WHERE to_phone = ? AND read = 0 ORDER BY sent DESC', (phone,))
            else:
                cursor.execute('SELECT * FROM messages WHERE to_phone = ? ORDER BY sent DESC LIMIT 20', (phone,))
            
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
    
    def mark_messages_read(self, phone):
        """Mark all messages as read"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE messages SET read = 1 WHERE to_phone = ?', (phone,))
            conn.commit()
            conn.close()
    
    def create_trade(self, from_phone, to_phone, offer):
        """Create trade offer"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO trades (from_phone, to_phone, offer_points, offer_pets, request_points, request_pets)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                from_phone, to_phone,
                offer.get('points', 0),
                json.dumps(offer.get('pets', [])),
                offer.get('request_points', 0),
                json.dumps(offer.get('request_pets', []))
            ))
            trade_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return trade_id
    
    def get_trade(self, trade_id):
        """Get trade by ID"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM trades WHERE id = ?', (trade_id,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
    
    def update_trade(self, trade_id, status):
        """Update trade status"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE trades SET status = ? WHERE id = ?', (status, trade_id))
            conn.commit()
            conn.close()
    
    def get_pending_trades(self, phone):
        """Get pending trades for player"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM trades 
                WHERE (to_phone = ? OR from_phone = ?) AND status = 'pending'
                ORDER BY created DESC
            ''', (phone, phone))
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
    
    def log_admin_action(self, admin_phone, action, target_phone, details):
        """Log admin action"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO admin_logs (admin_phone, action, target_phone, details)
                VALUES (?, ?, ?, ?)
            ''', (admin_phone, action, target_phone, details))
            conn.commit()
            conn.close()
    
    def get_global_stat(self, key):
        """Get global stat"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM global_stats WHERE key = ?', (key,))
            row = cursor.fetchone()
            conn.close()
            return row['value'] if row else None
    
    def set_global_stat(self, key, value):
        """Set global stat"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO global_stats (key, value, updated)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (key, value))
            conn.commit()
            conn.close()
    
    def _row_to_dict(self, row):
        """Convert sqlite row to dictionary"""
        d = dict(row)
        # Parse JSON fields
        json_fields = ['pets', 'inventory', 'used_codes', 'active_effects', 'chat_state']
        for field in json_fields:
            if field in d and d[field]:
                try:
                    d[field] = json.loads(d[field])
                except:
                    d[field] = [] if field != 'active_effects' else {}
        return d

# Singleton instance
db = Database()
'''

with open('core/database.py', 'w') as f:
    f.write(database_content)

print("✅ core/database.py created!")
print("🗄️  SQLite database - no external setup needed!")