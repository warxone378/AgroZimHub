# __init__.py
import os

# Ensure instance folder and database file exist
INSTANCE_PATH = '/opt/render/project/src/instance'
if not os.path.exists(INSTANCE_PATH):
    os.makedirs(INSTANCE_PATH, exist_ok=True)
    # Create an empty agrozim.db file
    open(os.path.join(INSTANCE_PATH, 'agrozim.db'), 'a').close()
