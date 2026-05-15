import requests
from config import GEMINI_API_KEY

class AIEngine:
    @staticmethod
    def predict_planting_strategy(province, seed_type, hectares, soil_type, soil_ph):
        prompt = f"""You are an expert Zimbabwean agronomist. Give a short, practical planting recommendation for:
Province: {province}
Seed: {seed_type}
Hectares: {hectares}
Soil: {soil_type}
pH: {soil_ph}
Provide: soil amendment, seed rate, fertilizer, irrigation, expected yield. Keep under 200 words."""

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.7, "maxOutputTokens": 300}}

        ai_advice = None
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=15)
            if resp.status_code == 200:
                ai_advice = resp.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                ai_advice = None  # fallback to rule-based
        except:
            ai_advice = None

        # --- Rule‑based fallback (no API) ---
        def rule_based():
            # pH advice
            if soil_ph < 5.5:
                ph_advice = f"⚠️ Soil pH {soil_ph} is acidic. Apply lime (2-3 tons/ha)."
            elif soil_ph > 7.5:
                ph_advice = f"⚠️ Soil pH {soil_ph} is alkaline. Add organic matter or sulfur."
            else:
                ph_advice = f"✅ Soil pH {soil_ph} is optimal."

            soil_advice = {
                'Sandy': "Low water retention. Irrigate every 3-5 days. Add compost.",
                'Clay': "Good water retention, poor drainage. Practice conservation tillage.",
                'Loam': "Ideal soil. Standard practices.",
                'Silty': "Fertile but prone to erosion. Use contour farming.",
                'Peaty': "High organic matter. Manage water levels."
            }.get(soil_type, "Standard practices.")

            seed_advice = {
                'Hybrid Maize': "Plant 25,000-30,000 plants/ha. Apply basal fertilizer 200kg/ha.",
                'Open Pollinated Maize': "Plant 22,000-25,000 plants/ha. Less fertilizer.",
                'Wheat': "Plant 120-150kg seed/ha. Requires cool temperatures.",
                'Soybean': "Inoculate seeds. Plant 40-50kg/ha.",
                'Sorghum': "Drought tolerant. Plant 8-10kg/ha."
            }.get(seed_type, "Follow standard guidelines.")

            province_advice = {
                'Manicaland': "High rainfall. Ensure drainage.",
                'Matabeleland North': "Drier. Use drought-resistant varieties.",
                'Matabeleland South': "Arid. Implement water harvesting.",
                'Mashonaland West': "Prime agricultural region.",
                'Mashonaland East': "Good for maize/horticulture.",
                'Mashonaland Central': "Good for cotton/maize.",
                'Midlands': "Moderate rainfall. Good for maize/soybeans.",
                'Masvingo': "Low rainfall. Drought-tolerant crops.",
                'Harare': "Urban farming. High value crops.",
                'Bulawayo': "Short season varieties ideal."
            }.get(province, "Standard practices.")

            fertilizer_kg = round(hectares * 200, 2)
            total_seed_kg = round(hectares * (25 if 'Maize' in seed_type else 15), 2)
            base_yield = 6.0
            if soil_type == 'Loam':
                yield_multiplier = 1.2
            elif soil_type == 'Clay':
                yield_multiplier = 1.0
            elif soil_type == 'Sandy':
                yield_multiplier = 0.7
            else:
                yield_multiplier = 0.9
            if soil_ph < 5.5 or soil_ph > 7.5:
                yield_multiplier *= 0.8
            expected_yield = round(hectares * base_yield * yield_multiplier, 2)

            return {
                'ph_advice': ph_advice,
                'soil_advice': soil_advice,
                'seed_advice': seed_advice,
                'province_advice': province_advice,
                'fertilizer_kg': fertilizer_kg,
                'total_seed_kg': total_seed_kg,
                'expected_yield_tons': expected_yield,
                'irrigation_advice': "Irrigate every 3-5 days" if soil_type == 'Sandy' else "Irrigate weekly or as needed"
            }

        # Use Gemini if available, else rule‑based
        if ai_advice:
            # Keep numerical parts from rule‑based, but add AI text
            fallback = rule_based()
            return {
                'ph_advice': ai_advice[:300] + "..." if len(ai_advice) > 300 else ai_advice,
                'soil_advice': ai_advice,
                'seed_advice': ai_advice,
                'province_advice': ai_advice,
                'fertilizer_kg': fallback['fertilizer_kg'],
                'total_seed_kg': fallback['total_seed_kg'],
                'expected_yield_tons': fallback['expected_yield_tons'],
                'irrigation_advice': fallback['irrigation_advice']
            }
        else:
            return rule_based()
