import requests
from config import WEATHER_API_KEY, PROVINCE_CITY

class WeatherService:
    @staticmethod
    def get_weather_data(city=None):
        """Fetch weather for a given city. If None, use user's province mapping."""
        if not city:
            # Fallback to Harare if no city provided
            city = "Harare,ZW"
        
        # If no API key or placeholder, return simulated data
        if WEATHER_API_KEY == "YOUR_OPENWEATHER_API_KEY":
            return {
                'temperature': 28,
                'humidity': 65,
                'condition': 'Partly cloudy',
                'rain_mm': 0,
                'wind_speed': 12,
                'city': city
            }
        
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                weather = {
                    'temperature': data['main']['temp'],
                    'humidity': data['main']['humidity'],
                    'condition': data['weather'][0]['description'],
                    'rain_mm': data.get('rain', {}).get('1h', 0),
                    'wind_speed': data['wind']['speed'],
                    'city': city
                }
                return weather
            else:
                # Fallback to simulated on error
                return {
                    'temperature': 28,
                    'humidity': 65,
                    'condition': 'Partly cloudy (API error)',
                    'rain_mm': 0,
                    'wind_speed': 12,
                    'city': city
                }
        except Exception as e:
            print(f"Weather API error: {e}")
            return None

    @staticmethod
    def analyze_weather_risks(weather_data):
        if not weather_data:
            return {
                'flood_risk': 'unknown',
                'dry_spell_risk': 'unknown',
                'suggestions': ['Weather data unavailable'],
                'weather_summary': 'No data'
            }
        suggestions = []
        flood_risk = 'low'
        dry_spell_risk = 'low'
        
        if weather_data['rain_mm'] > 20:
            flood_risk = 'high'
            suggestions.append(f"Heavy rain alert in {weather_data.get('city', 'your area')}. Potential flooding.")
        elif weather_data['rain_mm'] > 10:
            flood_risk = 'medium'
            suggestions.append("Moderate rain. Monitor water levels.")
        
        if weather_data['temperature'] > 32 and weather_data['humidity'] < 30:
            dry_spell_risk = 'high'
            suggestions.append("Extreme dry spell. Increase irrigation and apply mulch.")
        elif weather_data['temperature'] > 30 and weather_data['humidity'] < 40:
            dry_spell_risk = 'medium'
            suggestions.append("Dry conditions. Early morning irrigation recommended.")
        
        if not suggestions:
            suggestions.append("Current weather favorable for farming.")
        
        return {
            'flood_risk': flood_risk,
            'dry_spell_risk': dry_spell_risk,
            'suggestions': suggestions,
            'weather_summary': f"{weather_data['temperature']}°C, {weather_data['condition']}, Humidity: {weather_data['humidity']}% in {weather_data.get('city', 'your area')}"
        }
