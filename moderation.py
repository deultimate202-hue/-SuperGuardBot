import time
import re
from database import get_user_state, update_user_state

def check_flood(chat_id, user_id, settings):
    if not settings["anti_flood"]:
        return False, 0
        
    state = get_user_state(chat_id, user_id)
    current_time = time.time()
    
    # Reset count if last message was more than 4 seconds ago
    if current_time - state["last_msg_time"] > 4:
        state["msg_count"] = 1
    else:
        state["msg_count"] += 1
        
    state["last_msg_time"] = current_time
    update_user_state(chat_id, user_id, state)
    
    # Limit: 5 messages per 4 seconds
    is_flooding = state["msg_count"] > 5
    return is_flooding, state["msg_count"]

def check_spam(text, settings):
    if not settings["anti_spam"] or not text:
        return False
        
    text_lower = text.lower()
    
    # Check blocked words (using word boundaries to avoid false positives)
    for word in settings["blocked_words"]:
        if re.search(r'\b' + re.escape(word.lower()) + r'\b', text_lower):
            return True
            
    # Check blocked domains
    for domain in settings["blocked_domains"]:
        if domain.lower() in text_lower:
            return True
            
    return False
