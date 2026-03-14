
# core/trading_system.py
trading_code = r'''import json
from datetime import datetime
from core.database import db
from utils.helpers import format_number, mask_phone

class TradingSystem:
    def __init__(self, config):
        self.config = config
    
    def send_trade_request(self, from_phone, to_phone, offer_text):
        """
        Create a trade request
        Format: trade [phone] [offer]
        Example: trade 1234567890 500 points for my wolf
        """
        # Check if target exists
        target = db.get_player(to_phone)
        if target['points'] == 1000 and target['wins'] == 0 and len(target['pets']) == 0:
            # Check if truly new or just inactive
            pass  # Allow trading with new players
        
        # Parse offer text
        offer = self._parse_offer(from_phone, offer_text)
        
        if not offer:
            return "❌ Could not understand trade offer!\nFormat: trade [phone] [what you offer] for [what you want]\nExample: trade 1234567890 500 points and my Slime for your Wolf"
        
        # Check if sender has what they're offering
        sender = db.get_player(from_phone)
        
        if offer['points'] > sender['points']:
            return f"❌ You don't have {format_number(offer['points'])}💰!"
        
        for pet_name in offer['pets']:
            if not any(p['name'].lower() == pet_name.lower() for p in sender['pets']):
                return f"❌ You don't have a pet named '{pet_name}'!"
        
        # Create trade
        trade_id = db.create_trade(from_phone, to_phone, offer)
        
        # Notify target
        from core.messaging import messaging
        sender_masked = mask_phone(from_phone)
        
        offer_desc = f"{format_number(offer['points'])}💰" if offer['points'] > 0 else ""
        if offer['pets']:
            if offer_desc:
                offer_desc += " + "
            offer_desc += ", ".join(offer['pets'])
        
        request_desc = f"{format_number(offer.get('request_points', 0))}💰" if offer.get('request_points', 0) > 0 else ""
        if offer.get('request_pets'):
            if request_desc:
                request_desc += " + "
            request_desc += ", ".join(offer['request_pets'])
        
        if not request_desc:
            request_desc = "Nothing specific"
        
        messaging.send_message(
            to_phone,
            f"""
🤝 *TRADE OFFER* 🤝

From: {sender_masked}
Trade ID: {trade_id}

They offer:
{offer_desc}

They want:
{request_desc}

To accept: trade accept {trade_id}
To decline: trade decline {trade_id}
            """.strip()
        )
        
        return f"""
📨 *TRADE SENT!*

Trade ID: {trade_id}
To: {mask_phone(to_phone)}

Offer: {offer_desc}
Request: {request_desc}

Waiting for response...
        """.strip()
    
    def _parse_offer(self, phone, text):
        """Parse trade offer text"""
        offer = {'points': 0, 'pets': [], 'request_points': 0, 'request_pets': []}
        
        # Simple parser - look for numbers as points
        import re
        numbers = re.findall(r'\d+', text)
        
        # First number is usually offer
        if numbers:
            offer['points'] = int(numbers[0])
        
        # Look for "for" or "want" to separate offer/request
        text_lower = text.lower()
        
        # Get player's pets to match names
        player = db.get_player(phone)
        pet_names = [p['name'].lower() for p in player['pets']]
        
        # Check for pet names in text
        for pet_name in pet_names:
            if pet_name in text_lower:
                offer['pets'].append(pet_name.title())
        
        return offer if (offer['points'] > 0 or offer['pets']) else None
    
    def respond_to_trade(self, phone, trade_id, accept):
        """Accept or decline trade"""
        trade = db.get_trade(trade_id)
        
        if not trade:
            return "❌ Trade not found! Check the Trade ID."
        
        if trade['to_phone'] != phone and trade['from_phone'] != phone:
            return "❌ This trade is not for you!"
        
        if trade['status'] != 'pending':
            return f"❌ Trade already {trade['status']}!"
        
        if accept:
            # Process trade
            from_player = db.get_player(trade['from_phone'])
            to_player = db.get_player(trade['to_phone'])
            
            offer_pets = json.loads(trade['offer_pets'])
            request_pets = json.loads(trade['request_pets'])
            
            # Verify from_player still has offer
            if trade['offer_points'] > from_player['points']:
                db.update_trade(trade_id, 'failed')
                return "❌ Trade failed! Sender doesn't have enough points anymore."
            
            for pet_name in offer_pets:
                if not any(p['name'].lower() == pet_name.lower() for p in from_player['pets']):
                    db.update_trade(trade_id, 'failed')
                    return f"❌ Trade failed! Sender doesn't have {pet_name} anymore."
            
            # Transfer points
            from_player['points'] -= trade['offer_points']
            to_player['points'] += trade['offer_points']
            
            if trade['request_points'] > 0:
                if trade['request_points'] > to_player['points']:
                    db.update_trade(trade_id, 'failed')
                    return "❌ Trade failed! You don't have enough points!"
                to_player['points'] -= trade['request_points']
                from_player['points'] += trade['request_points']
            
            # Transfer pets - offer (from -> to)
            for pet_name in offer_pets:
                for i, pet in enumerate(from_player['pets']):
                    if pet['name'].lower() == pet_name.lower():
                        to_player['pets'].append(pet)
                        from_player['pets'].pop(i)
                        break
            
            # Transfer pets - request (to -> from)
            for pet_name in request_pets:
                for i, pet in enumerate(to_player['pets']):
                    if pet['name'].lower() == pet_name.lower():
                        from_player['pets'].append(pet)
                        to_player['pets'].pop(i)
                        break
            
            # Save
            db.save_player(trade['from_phone'], from_player)
            db.save_player(trade['to_phone'], to_player)
            db.update_trade(trade_id, 'accepted')
            
            # Notify other party
            from core.messaging import messaging
            other_phone = trade['from_phone'] if phone == trade['to_phone'] else trade['to_phone']
            messaging.send_message(other_phone, f"✅ *TRADE ACCEPTED!*\n\nTrade #{trade_id} completed successfully!")
            
            return f"""
✅ *TRADE COMPLETED!* ✅

Trade #{trade_id}
Status: Accepted

You received:
{format_number(trade['offer_points'])}💰
{', '.join(offer_pets) if offer_pets else ''}
            """.strip()
        
        else:
            # Decline
            db.update_trade(trade_id, 'declined')
            
            # Notify sender
            from core.messaging import messaging
            messaging.send_message(trade['from_phone'], f"❌ *TRADE DECLINED*\n\nTrade #{trade_id} was declined by {mask_phone(phone)}")
            
            return f"❌ Trade #{trade_id} declined."
    
    def list_trades(self, phone):
        """List pending trades"""
        trades = db.get_pending_trades(phone)
        
        if not trades:
            return "📭 No pending trades!\n\nTo trade: trade [phone] [your offer] for [their offer]"
        
        message = "📋 *YOUR TRADES*\n\n"
        
        for trade in trades:
            is_sender = trade['from_phone'] == phone
            other = trade['to_phone'] if is_sender else trade['from_phone']
            direction = "→" if is_sender else "←"
            
            offer_pets = json.loads(trade['offer_pets'])
            offer_text = f"{format_number(trade['offer_points'])}💰"
            if offer_pets:
                offer_text += f" + {len(offer_pets)} pets"
            
            message += f"#{trade['id']} {direction} {mask_phone(other)}\n"
            message += f"   Offer: {offer_text}\n"
            if not is_sender:
                message += f"   Accept: trade accept {trade['id']}\n"
            message += "\n"
        
        return message
    
    def send_message_to_player(self, from_phone, to_phone, message_text):
        """Send private message to another player"""
        # Check if target exists
        target = db.get_player(to_phone)
        
        # Save message
        db.send_message(from_phone, to_phone, message_text, 'private')
        
        # Notify target
        from core.messaging import messaging
        messaging.send_message(
            to_phone,
            f"""
💬 *NEW MESSAGE* 💬

From: {mask_phone(from_phone)}
"{message_text[:100]}{'...' if len(message_text) > 100 else ''}"

Reply: msg {from_phone} [your message]
View inbox: inbox
            """.strip()
        )
        
        return f"📨 Message sent to {mask_phone(to_phone)}!"
    
    def get_inbox(self, phone):
        """Get player messages"""
        messages = db.get_messages(phone)
        
        if not messages:
            return "📭 Your inbox is empty!\n\nSend messages: msg [phone] [message]"
        
        message = "📬 *YOUR INBOX*\n\n"
        
        unread = sum(1 for m in messages if not m['read'])
        if unread > 0:
            message += f"🔔 {unread} unread messages\n\n"
        
        for msg in messages[:5]:
            status = "🔴" if not msg['read'] else "✓"
            time = msg['sent'][:16] if isinstance(msg['sent'], str) else msg['sent'].strftime('%m/%d %H:%M')
            message += f"{status} {time} - {mask_phone(msg['from_phone'])}\n"
            preview = msg['message'][:30] + "..." if len(msg['message']) > 30 else msg['message']
            message += f"   \"{preview}\"\n\n"
        
        if len(messages) > 5:
            message += f"...and {len(messages) - 5} more\n"
        
        message += "\nMark as read: read"
        
        # Mark as read
        db.mark_messages_read(phone)
        
        return message
'''

with open('core/trading_system.py', 'w') as f:
    f.write(trading_code)

print("✅ core/trading_system.py created!")