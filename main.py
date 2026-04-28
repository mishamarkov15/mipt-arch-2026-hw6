from converters import CurrencyConversionError, CurrencyConverter


TARGET_CURRENCIES = ("RUB", "EUR", "GBP", "CNY")


def read_amount() -> float:
    raw_amount = input("Введите значение в USD:\n")

    try:
        amount = float(raw_amount)
    except ValueError as error:
        raise ValueError("Введите числовое значение") from error

    if amount < 0:
        raise ValueError("Значение не может быть отрицательным")

    return amount


def main():
    try:
        amount = read_amount()
        converter = CurrencyConverter()
        converted_amounts = converter.convert_many(amount, TARGET_CURRENCIES)
    except (CurrencyConversionError, ValueError) as error:
        print(f"Ошибка: {error}")
        return

    for currency, converted_amount in converted_amounts.items():
        print(f"{amount:.2f} USD to {currency}: {converted_amount:.2f}")


if __name__ == "__main__":
    main()
