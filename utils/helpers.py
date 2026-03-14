# utils/helpers.py
helpers_code = r'''import random
import json
from datetime import datetime, timedelta

def format_number(num):
    """Format large numbers with K, M, B"""
    if num >= 1_000_000_000:
        return f"{num/1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    return str(num)

def get_rarity_color(rarity):
    """Get emoji color for rarity"""
    colors = {
        'common': '⬛',
        'rare': '🟩', 
        'epic': '🟨',
        'legendary': '🟪',
        'mythic': '🟥'
    }
    return colors.get(rarity.lower(), '⬜')

def calculate_level_up_exp(level):
    """Calculate EXP needed for next level"""
    return int(100 * (1.5 ** (level - 1)))

def parse_damage_range(damage_str):
    """Parse '10-20' into min, max"""
    parts = damage_str.split('-')
    return int(parts[0]), int(parts[1])

def roll_chance(percentage):
    """Roll for percentage chance"""
    return random.randint(1, 100) <= percentage

def get_time_left(target_time):
    """Get human readable time left"""
    if not target_time:
        return "Available"
    
    if isinstance(target_time, str):
        target_time = datetime.fromisoformat(target_time)
    
    now = datetime.now()
    if target_time <= now:
        return "Available"
    
    diff = target_time - now
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    
    if diff.days > 0:
        return f"{diff.days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

def truncate_text(text, max_length=20):
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def generate_battle_bar(current, maximum, length=10):
    """Generate HP/EXP bar"""
    if maximum <= 0:
        return "░" * length
    filled = int((current / maximum) * length)
    filled = max(0, min(filled, length))
    return "█" * filled + "░" * (length - filled)

def mask_phone(phone):
    """Mask phone number for privacy"""
    if len(phone) <= 4:
        return "****"
    return phone[:2] + "****" + phone[-2:]
'''

with open('utils/helpers.py', 'w') as f:
    f.write(helpers_code)

print("✅ utils/helpers.py created!")