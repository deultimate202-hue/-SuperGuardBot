import time
import re
from database import get_user_state, update_user_state

def check_message_rate(chat_id, user_id, settings):
    if not settings["rate_limit_enabled"]:
        return False, 0
        
    state = get_user_state(chat_id, user_id)
    current_time = time.time()
    
    if current_time - state["last_msg_time"] > 4:
        state["msg_count"] = 1
    else:
        state["msg_count"] += 1
        
    state["last_msg_time"] = current_time
    update_user_state(chat_id, user_id, state)
    
    is_rate_limited = state["msg_count"] > 5
    return is_rate_limited, state["msg_count"]

def check_content_policy(text, settings):
    if not settings["content_filter_enabled"] or not text:
        return False
        
    text_lower = text.lower()
    
    for term in settings["filtered_terms"]:
        if re.search(r'\b' + re.escape(term.lower()) + r'\b', text_lower):
            return True
            
    for domain in settings["filtered_domains"]:
        if domain.lower() in text_lower:
            return True
            
    return False
