import secrets, time, hashlib, json, os

TOKEN_FILE = 'data/reset_tokens.json'

def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return json.load(f)
    return {}

def save_tokens(tokens):
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f)

def generate_reset_token(user_id):
    token = secrets.token_urlsafe(32)
    tokens = load_tokens()
    tokens[token] = {'user_id': user_id, 'expires': time.time() + 3600}  # 1 hour
    save_tokens(tokens)
    return token

def verify_reset_token(token):
    tokens = load_tokens()
    data = tokens.get(token)
    if data and data['expires'] > time.time():
        return data['user_id']
    return None

def delete_token(token):
    tokens = load_tokens()
    if token in tokens:
        del tokens[token]
        save_tokens(tokens)
