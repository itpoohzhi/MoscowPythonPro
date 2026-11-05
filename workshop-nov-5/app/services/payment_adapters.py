import hashlib
import logging

logger = logging.getLogger(__name__)


class StripePaymentGateway:
    """Адаптер интеграции с платежной системой Stripe."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def process_external_charge(self, token: str, amount: int) -> str:
        masked_token = f"{token[:4]}***" if len(token) > 4 else "***"
        logger.info("Обращение к Stripe API: списание %s коп. по токену %s", amount, masked_token)
        # В продакшене здесь выполняется асинхронный HTTP POST запрос к api.stripe.com
        token_fp = hashlib.sha256(token.encode("utf-8")).hexdigest()[:8]
        return f"ch_stripe_{token_fp}_{amount}"


class MockPaymentGateway:
    """Тестовый симулятор платежного шлюза (Test Double)."""

    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.processed_charges = []

    async def process_external_charge(self, token: str, amount: int) -> str:
        if self.should_fail:
            raise ConnectionError("Платежный шлюз временно недоступен (503)")
        tx_id = f"tx_mock_{len(self.processed_charges) + 1}"
        self.processed_charges.append((token, amount, tx_id))
        return tx_id
