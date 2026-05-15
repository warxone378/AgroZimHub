import os

# Hardcoded secret key (no environment variable needed)
SECRET_KEY = "demo-secret-key-12345"
DEBUG = False

# Use instance folder (Render allows writes here)
INSTANCE_PATH = '/opt/render/project/src/instance'
os.makedirs(INSTANCE_PATH, exist_ok=True)
SQLALCHEMY_DATABASE_URI = f'sqlite:///{INSTANCE_PATH}/agrozim.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

WEATHER_API_KEY = '21a19f388c785be5a6e02fbf77f130e5'

PROVINCES = ['Bulawayo','Harare','Manicaland','Mashonaland Central','Mashonaland East',
             'Mashonaland West','Masvingo','Matabeleland North','Matabeleland South','Midlands']
SOIL_TYPES = ['Sandy','Clay','Loam','Silty','Peaty']
SEED_TYPES = ['Hybrid Maize','Open Pollinated Maize','Wheat','Soybean','Sorghum']
