from converters import CurrencyConverter


class UsdEurConverter(CurrencyConverter):
    def convert_usd_to_eur(self, amount):
        return self.convert(amount, "EUR")
