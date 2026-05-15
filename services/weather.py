import requests
from config import WEATHER_API_KEY

class WeatherService:
    @staticmethod
    def get_weather_data(city="Harare,ZW"):
        if not WEATHER_API_KEY or WEATHER_API_KEY == "21a19f388c785be5a6e02fbf77f130e5":
            # Simulated when no key
            return {'temperature': 28, 'humidity': 65, 'condition': 'Partly cloudy', 'rain_mm': 0}
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                d = r.json()
                return {
                    'temperature': d['main']['temp'],
                    'humidity': d['main']['humidity'],
                    'condition': d['weather'][0]['description'],
                    'rain_mm': d.get('rain', {}).get('1h', 0)
                }
        except:
            pass
        return {'temperature': 28, 'humidity': 65, 'condition': 'Partly cloudy', 'rain_mm': 0}

    @staticmethod
    def analyze_weather_risks(weather):
        if not weather:
            return {'flood_risk': 'unknown', 'dry_spell_risk': 'unknown', 'suggestions': ['Weather data unavailable']}
        suggestions = []
        flood = 'low'
        dry = 'low'
        if weather['rain_mm'] > 20:
            flood = 'high'
            suggestions.append("⚠️ Heavy rain – potential flooding.")
        elif weather['rain_mm'] > 10:
            flood = 'medium'
            suggestions.append("Moderate rain. Clear drainage.")
        if weather['temperature'] > 32 and weather['humidity'] < 30:
            dry = 'high'
            suggestions.append("🔥 Extreme dry spell. Increase irrigation.")
        elif weather['temperature'] > 30:
            dry = 'medium'
            suggestions.append("Dry conditions. Water early morning.")
        if not suggestions:
            suggestions.append("✅ Weather favorable.")
        return {'flood_risk': flood, 'dry_spell_risk': dry, 'suggestions': suggestions}
