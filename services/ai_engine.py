class AIEngine:
    @staticmethod
    def predict_planting_strategy(province, seed_type, hectares, soil_type, soil_ph):
        if soil_ph < 5.5:
            ph_advice = f"⚠️ Acidic soil (pH {soil_ph}). Apply lime at 2-3 tons/ha."
        elif soil_ph > 7.5:
            ph_advice = f"⚠️ Alkaline soil (pH {soil_ph}). Add organic matter or sulfur."
        else:
            ph_advice = f"✅ Optimal pH {soil_ph}."
        soil_advice = {
            'Sandy': 'Low water retention. Irrigate every 3-5 days, add compost.',
            'Clay': 'Good retention but poor drainage. Use raised beds.',
            'Loam': 'Ideal soil. Standard practices.',
        }.get(soil_type, 'Standard practices.')
        seed_advice = {
            'Hybrid Maize': 'Plant 25,000-30,000 plants/ha. Apply basal fertilizer 200kg/ha.',
            'Wheat': 'Plant 120-150kg seed/ha. Requires cool weather.',
        }.get(seed_type, 'Follow standard planting guidelines.')
        fertilizer = round(float(hectares) * 200, 2)
        seed_kg = round(float(hectares) * 25, 2)
        yield_tons = round(float(hectares) * 6.0, 2)
        return {
            'ph_advice': ph_advice,
            'soil_advice': soil_advice,
            'seed_advice': seed_advice,
            'fertilizer_kg': fertilizer,
            'total_seed_kg': seed_kg,
            'expected_yield_tons': yield_tons
        }
