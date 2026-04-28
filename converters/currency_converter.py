import json
import logging
import time
from pathlib import Path
from typing import Iterable, Protocol

import requests


API_URL = "https://api.exchangerate-api.com/v4/latest/{base_currency}"
DEFAULT_BASE_CURRENCY = "USD"
DEFAULT_CACHE_FILE = "exchange_rates.json"


class CurrencyConversionError(RuntimeError):
    """Raised when exchange rates cannot be loaded or used."""


class ExchangeRateProvider(Protocol):
    def get_rates(self, base_currency: str) -> dict[str, float]:
        """Return exchange rates for the selected base currency."""


class RequestsExchangeRateProvider:
    def __init__(
        self,
        api_url: str = API_URL,
        timeout: int = 10,
        max_retries: int = 3,
        retry_delay: int = 2,
        logger: logging.Logger | None = None,
    ):
        self.api_url = api_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logger or logging.getLogger(__name__)

    def get_rates(self, base_currency: str) -> dict[str, float]:
        url = self.api_url.format(base_currency=base_currency)

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                return data["rates"]
            except (requests.RequestException, ValueError, KeyError) as error:
                self.logger.warning(
                    "Could not fetch exchange rates, attempt %s/%s: %s",
                    attempt,
                    self.max_retries,
                    error,
                )
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)

        raise CurrencyConversionError("Exchange rates are unavailable")


class CachedExchangeRateProvider:
    def __init__(
        self,
        provider: ExchangeRateProvider | None = None,
        cache_file: str | Path = DEFAULT_CACHE_FILE,
        cache_ttl_seconds: int = 3600,
        clock=time.time,
    ):
        self.provider = provider or RequestsExchangeRateProvider()
        self.cache_file = Path(cache_file)
        self.cache_ttl_seconds = cache_ttl_seconds
        self.clock = clock

    def get_rates(self, base_currency: str) -> dict[str, float]:
        cached_rates = self._load_from_cache(base_currency)
        if cached_rates is not None:
            return cached_rates

        rates = self.provider.get_rates(base_currency)
        self._save_to_cache(base_currency, rates)
        return rates

    def _load_from_cache(self, base_currency: str) -> dict[str, float] | None:
        if not self.cache_file.exists():
            return None

        try:
            with self.cache_file.open(encoding="utf-8") as file:
                cached = json.load(file)
        except (OSError, ValueError):
            return None

        is_same_currency = cached.get("base_currency") == base_currency
        is_fresh = self.clock() - cached.get("timestamp", 0) < self.cache_ttl_seconds
        rates = cached.get("rates")
        if is_same_currency and is_fresh and isinstance(rates, dict):
            return rates

        return None

    def _save_to_cache(self, base_currency: str, rates: dict[str, float]) -> None:
        cache = {
            "base_currency": base_currency,
            "timestamp": self.clock(),
            "rates": rates,
        }

        try:
            with self.cache_file.open("w", encoding="utf-8") as file:
                json.dump(cache, file)
        except OSError:
            pass


class CurrencyConverter:
    def __init__(
        self,
        provider: ExchangeRateProvider | None = None,
        base_currency: str = DEFAULT_BASE_CURRENCY,
    ):
        self.provider = provider or CachedExchangeRateProvider()
        self.base_currency = base_currency
        self._rates: dict[str, float] | None = None

    def convert(self, amount: float, target_currency: str) -> float:
        if amount < 0:
            raise ValueError("Amount must not be negative")

        rates = self._get_rates()
        target_currency = target_currency.upper()

        try:
            return amount * rates[target_currency]
        except KeyError as error:
            raise CurrencyConversionError(
                f"Unsupported target currency: {target_currency}"
            ) from error

    def convert_many(
        self,
        amount: float,
        target_currencies: Iterable[str],
    ) -> dict[str, float]:
        return {
            currency.upper(): self.convert(amount, currency)
            for currency in target_currencies
        }

    def _get_rates(self) -> dict[str, float]:
        if self._rates is None:
            self._rates = self.provider.get_rates(self.base_currency)

        return self._rates
