import os

SECRET_KEY = "demo-secret-key-12345"
DEBUG = False

# Use /tmp/ – fully writable on Render (data lost on restart, ok for demo)
SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/agrozim.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

WEATHER_API_KEY = '21a19f388c785be5a6e02fbf77f130e5'

PROVINCES = ['Bulawayo','Harare','Manicaland','Mashonaland Central','Mashonaland East',
             'Mashonaland West','Masvingo','Matabeleland North','Matabeleland South','Midlands']
SOIL_TYPES = ['Sandy','Clay','Loam','Silty','Peaty']
SEED_TYPES = ['Hybrid Maize','Open Pollinated Maize','Wheat','Soybean','Sorghum']
