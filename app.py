import os
import random
import string
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

# Filepath for your persistent JSON storage
DB_FILE = "keys.json"

def load_keys():
    """Loads the keys database from the JSON file into memory."""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            # If file is corrupted or empty, fall back to empty dictionary
            return {}
    return {}

def save_keys(data):
    """Saves the current memory state of keys back to the JSON file."""
    try:
        with open(DB_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error writing to persistent storage file: {e}")

# Initialize memory space by loading any pre-existing keys from disk
keys_db = load_keys()

def generate_random_key(tool, plan):
    """Generates a unique key like: CODM-1DAY-XXXX-XXXX"""
    prefix = f"{tool.upper()}-{plan.replace(' ', '').upper()}-"
    random_part = '-'.join(''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(2))
    return prefix + random_part

@app.route('/')
def index():
    # Fresh database pull to ensure frontend template accurately mirrors data
    current_keys = load_keys()
    return render_template('index.html', keys=current_keys)

@app.route('/generate', methods=['POST'])
def generate():
    global keys_db
    tool = request.form.get('tool')
    plan = request.form.get('plan')
    
    if tool and plan:
        # Load latest data layer state before editing
        keys_db = load_keys()
        
        new_key = generate_random_key(tool, plan)
        keys_db[new_key] = {
            'tool': tool,
            'plan': plan,
            'status': 'Active'
        }
        # Commit new state directly to disk layer file
        save_keys(keys_db)
        
    return redirect(url_for('index'))

@app.route('/delete/<key_string>', methods=['POST'])
def delete_key(key_string):
    global keys_db
    keys_db = load_keys()
    
    if key_string in keys_db:
        del keys_db[key_string]
        # Commit updated collection map to file after removal item drop
        save_keys(keys_db)
        
    return redirect(url_for('index'))


# ==========================================
#  FIXED & ENHANCED API ENDPOINT FOR APP Connection
# ==========================================
@app.route('/api/validate', methods=['POST', 'GET'])
@app.route('/api/validate/<key_string>', methods=['GET'])
def validate_key(key_string=None):
    # Load freshest records state to cross-examine incoming verification checks
    current_keys = load_keys()

    # 1. Handle if key comes from JSON body (Common in Android requests)
    if request.is_json:
        data = request.get_json()
        key_string = data.get('key') or data.get('key_string')
    
    # 2. Handle if key comes from a Form submission POST parameter
    elif request.method == 'POST':
        key_string = request.form.get('key') or request.form.get('key_string')

    # 3. If no key was provided anywhere, reject immediately
    if not key_string:
        return jsonify({
            'valid': False, 
            'message': 'Authentication payload structural integrity error. Key parameter missing.'
        }), 400

    # 4. Strip out whitespace in case user copied a space by mistake
    key_string = key_string.strip()

    # 5. Core Verification Database Lookup Check
    if key_string in current_keys:
        return jsonify({
            'valid': True, 
            'message': 'Handshake verified successfully.',
            'data': current_keys[key_string]
        }), 200
        
    return jsonify({
        'valid': False, 
        'message': 'Key validation failure. Token either expired, revoked, or non-existent.'
    }), 404

if __name__ == '__main__':
    # Running on 0.0.0.0 makes it broadcast over the local network 
    # so your mobile device can see the server!
    app.run(debug=True, host='0.0.0.0', port=5000)
