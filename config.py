import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-12345')
DEBUG = False
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///agrozim.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY', '21a19f388c785be5a6e02fbf77f130e5')
PROVINCES = ['Bulawayo','Harare','Manicaland','Mashonaland Central','Mashonaland East',
             'Mashonaland West','Masvingo','Matabeleland North','Matabeleland South','Midlands']
SOIL_TYPES = ['Sandy','Clay','Loam','Silty','Peaty']
SEED_TYPES = ['Hybrid Maize','Open Pollinated Maize','Wheat','Soybean','Sorghum']
