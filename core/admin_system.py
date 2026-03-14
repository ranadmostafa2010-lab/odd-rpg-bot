# core/admin_system.py
admin_code = r'''import json
from datetime import datetime
from core.database import db
from utils.helpers import format_number

class AdminSystem:
    def __init__(self, config):
        self.config = config
        self.admin_phone = config.get('admin_phone', '')
        self.admin_commands = config.get('admin_commands', {})
    
    def is_admin(self, phone):
        """Check if phone is admin"""
        return phone == self.admin_phone
    
    def process_command(self, phone, command_text):
        """Process admin command"""
        if not self.is_admin(phone):
            return "⛔ Access denied! Admin only."
        
        parts = command_text.split()
        if not parts:
            return self._help_text()
        
        cmd = parts[0].lower()
        args = parts[1:]
        
        # Log admin action
        db.log_admin_action(phone, cmd, args[0] if args else 'none', ' '.join(args))
        
        if cmd == 'givepoints':
            return self._give_points(args)
        elif cmd == 'givepet':
            return self._give_pet(args)
        elif cmd == 'removepoints':
            return self._remove_points(args)
        elif cmd == 'ban':
            return self._ban_player(args)
        elif cmd == 'unban':
            return self._unban_player(args)
        elif cmd == 'broadcast':
            return self._broadcast(args)
        elif cmd == 'maintenance':
            return self._toggle_maintenance(args)
        elif cmd == 'reset':
            return self._reset_player(args)
        elif cmd == 'addcode':
            return self._add_code(args)
        elif cmd == 'spawnboss':
            return self._spawn_boss(args)
        elif cmd == 'giveitem':
            return self._give_item(args)
        elif cmd == 'stats':
            return self._global_stats()
        elif cmd == 'help':
            return self._help_text()
        else:
            return f"❓ Unknown admin command: {cmd}\nUse: admin help"
    
    def _give_points(self, args):
        """Give points to player"""
        if len(args) < 2:
            return "Usage: admin givepoints [phone] [amount]"
        
        target_phone = args[0]
        try:
            amount = int(args[1])
        except:
            return "❌ Invalid amount!"
        
        player = db.get_player(target_phone)
        player['points'] += amount
        db.save_player(target_phone, player)
        
        # Notify player
        from core.messaging import messaging
        messaging.send_message(target_phone, f"🎁 *ADMIN GIFT*\n\nYou received {format_number(amount)}💰 from admin!")
        
        return f"✅ Gave {format_number(amount)}💰 to {target_phone}\nNew balance: {format_number(player['points'])}💰"
    
    def _give_pet(self, args):
        """Give specific pet to player"""
        if len(args) < 3:
            return "Usage: admin givepet [phone] [pet_name] [rarity]"
        
        target_phone = args[0]
        pet_name = args[1]
        rarity = args[2].lower()
        
        player = db.get_player(target_phone)
        
        # Find pet template
        pets_config = self.config.get('pets', {})
        pet_template = None
        
        for r, pets in pets_config.items():
            if r == rarity:
                for p in pets:
                    if p['name'].lower() == pet_name.lower():
                        pet_template = p
                        break
        
        if not pet_template:
            # Create custom pet
            pet = {
                'name': pet_name,
                'emoji': '🎁',
                'atk': 100,
                'rarity': rarity,
                'level': 1,
                'exp': 0,
                'enchanted': True,
                'growth': 3.0
            }
        else:
            pet = {
                'name': pet_template['name'],
                'emoji': pet_template['emoji'],
                'atk': pet_template['base_atk'] * 2,
                'rarity': rarity,
                'level': 1,
                'exp': 0,
                'enchanted': True,
                'growth': pet_template.get('growth', 2.0)
            }
        
        player['pets'].append(pet)
        db.save_player(target_phone, player)
        
        # Notify
        from core.messaging import messaging
        messaging.send_message(target_phone, f"🎁 *ADMIN GIFT*\n\nYou received a {rarity.upper()} {pet_name} from admin!")
        
        return f"✅ Gave {rarity} {pet_name} to {target_phone}"
    
    def _remove_points(self, args):
        """Remove points from player"""
        if len(args) < 2:
            return "Usage: admin removepoints [phone] [amount]"
        
        target_phone = args[0]
        try:
            amount = int(args[1])
        except:
            return "❌ Invalid amount!"
        
        player = db.get_player(target_phone)
        player['points'] = max(0, player['points'] - amount)
        db.save_player(target_phone, player)
        
        return f"✅ Removed {format_number(amount)}💰 from {target_phone}\nNew balance: {format_number(player['points'])}💰"
    
    def _ban_player(self, args):
        """Ban a player"""
        if len(args) < 1:
            return "Usage: admin ban [phone] [reason]"
        
        target_phone = args[0]
        reason = ' '.join(args[1:]) if len(args) > 1 else 'No reason given'
        
        player = db.get_player(target_phone)
        player['banned'] = 1
        player['ban_reason'] = reason
        db.save_player(target_phone, player)
        
        return f"🚫 Banned {target_phone}\nReason: {reason}"
    
    def _unban_player(self, args):
        """Unban a player"""
        if len(args) < 1:
            return "Usage: admin unban [phone]"
        
        target_phone = args[0]
        
        player = db.get_player(target_phone)
        player['banned'] = 0
        player['ban_reason'] = None
        db.save_player(target_phone, player)
        
        return f"✅ Unbanned {target_phone}"
    
    def _broadcast(self, args):
        """Send message to all players"""
        if not args:
            return "Usage: admin broadcast [message]"
        
        message = ' '.join(args)
        players = db.get_all_players()
        
        from core.messaging import messaging
        count = 0
        for player in players:
            success, _ = messaging.send_message(
                player['phone'],
                f"📢 *BROADCAST* 📢\n\n{message}\n\n- Admin"
            )
            if success:
                count += 1
        
        return f"📢 Broadcast sent to {count} players!"
    
    def _toggle_maintenance(self, args):
        """Toggle maintenance mode"""
        if not args:
            return "Usage: admin maintenance [on/off]"
        
        state = args[0].lower()
        self.config['maintenance_mode'] = (state == 'on')
        
        # Save config
        with open('config/admin_config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
        
        return f"🔧 Maintenance mode: {state.upper()}"
    
    def _reset_player(self, args):
        """Reset player data"""
        if len(args) < 1:
            return "Usage: admin reset [phone]"
        
        target_phone = args[0]
        
        # Delete and recreate
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM players WHERE phone = ?", (target_phone,))
        conn.commit()
        conn.close()
        
        # Recreate
        db.get_player(target_phone)
        
        return f"🔄 Reset player {target_phone}"
    
    def _add_code(self, args):
        """Add new promo code"""
        if len(args) < 3:
            return "Usage: admin addcode [code] [points] [uses]"
        
        code = args[0].upper()
        try:
            points = int(args[1])
            uses = int(args[2])
        except:
            return "❌ Invalid points or uses!"
        
        # Add to game config
        game_config = self._load_game_config()
        game_config['promo_codes'][code] = {
            'points': points,
            'uses': uses,
            'active': True
        }
        
        self._save_game_config(game_config)
        
        return f"✅ Added code: {code}\nPoints: {format_number(points)}\nUses: {uses}"
    
    def _spawn_boss(self, args):
        """Force spawn a boss"""
        from core.boss_system import BossSystem
        boss_name = args[0] if args else None
        
        boss_sys = BossSystem(self._load_game_config())
        boss_id = boss_sys.spawn_boss(boss_name, force=True)
        
        return f"👹 Boss spawned! ID: {boss_id}"
    
    def _give_item(self, args):
        """Give shop item to player"""
        if len(args) < 3:
            return "Usage: admin giveitem [phone] [item_id] [quantity]"
        
        target_phone = args[0]
        item_id = args[1]
        try:
            qty = int(args[2])
        except:
            qty = 1
        
        game_config = self._load_game_config()
        shop = game_config.get('shop_items', {})
        
        if item_id not in shop:
            return f"❌ Item {item_id} not found!"
        
        player = db.get_player(target_phone)
        item = shop[item_id]
        
        for _ in range(qty):
            player['inventory'].append({
                'type': item_id,
                'name': item['name'],
                'emoji': item['emoji']
            })
        
        db.save_player(target_phone, player)
        
        return f"✅ Gave {qty}x {item['name']} to {target_phone}"
    
    def _global_stats(self):
        """Get global game stats"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM players")
        total_players = cursor.fetchone()['total']
        
        cursor.execute("SELECT SUM(points) as total FROM players")
        total_points = cursor.fetchone()['total'] or 0
        
        cursor.execute("SELECT SUM(bank) as total FROM players")
        total_bank = cursor.fetchone()['total'] or 0
        
        cursor.execute("SELECT SUM(wins) as total FROM players")
        total_wins = cursor.fetchone()['total'] or 0
        
        conn.close()
        
        return f"""
📊 *GLOBAL STATS* 📊

👥 Total Players: {total_players}
💰 Points in Circulation: {format_number(total_points)}
🏦 Banked Points: {format_number(total_bank)}
⚔️ Total Battles Won: {format_number(total_wins)}

💎 Total Wealth: {format_number(total_points + total_bank)}
        """.strip()
    
    def _help_text(self):
        """Admin help text"""
        return """
🔐 *ADMIN COMMANDS* 🔐

givepoints [phone] [amount] - Give points
givepet [phone] [name] [rarity] - Give pet
removepoints [phone] [amount] - Remove points
ban [phone] [reason] - Ban player
unban [phone] - Unban player
broadcast [message] - Message all players
maintenance [on/off] - Toggle maintenance
reset [phone] - Reset player data
addcode [code] [points] [uses] - Add promo code
spawnboss [name] - Force spawn boss
giveitem [phone] [item] [qty] - Give item
stats - Global statistics
help - This menu

All commands start with: admin [command]
        """.strip()
    
    def _load_game_config(self):
        """Load game config"""
        with open('config/game_config.json', 'r') as f:
            return json.load(f)
    
    def _save_game_config(self, config):
        """Save game config"""
        with open('config/game_config.json', 'w') as f:
            json.dump(config, f, indent=2)
'''

with open('core/admin_system.py', 'w') as f:
    f.write(admin_code)

print("✅ core/admin_system.py created!")