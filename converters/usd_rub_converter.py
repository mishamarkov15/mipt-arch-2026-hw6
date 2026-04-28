from converters import CurrencyConverter


class UsdRubConverter(CurrencyConverter):
    def convert_usd_to_rub(self, amount):
        return self.convert(amount, "RUB")
