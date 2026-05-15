class FintechLogic:
    USD_TO_ZIG = 25.0
    @classmethod
    def usd_to_zig(cls, usd):
        return round(usd * cls.USD_TO_ZIG, 2)
