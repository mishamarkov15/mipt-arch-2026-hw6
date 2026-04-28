from converters import CurrencyConverter


class UsdGbpConverter(CurrencyConverter):
    def convert_usd_to_gbp(self, amount):
        return self.convert(amount, "GBP")
