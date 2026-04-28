from converters import CurrencyConverter


class UsdCnyConverter(CurrencyConverter):
    def convert_usd_to_cny(self, amount):
        return self.convert(amount, "CNY")
