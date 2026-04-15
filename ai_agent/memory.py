memory_store = {}

def save_memory(user_id, message):
    memory_store.setdefault(user_id, [])
    memory_store[user_id].append(message)

def get_memory(user_id):
    return memory_store.get(user_id, [])
