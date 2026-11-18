import pytest

from app.schemas.billing import PlanType, WalletBalance
from app.services.billing import BillingService
from app.services.payment_adapters import StripePaymentGateway


class FaultyMockRepo:
    def __init__(self):
        self.wallet = WalletBalance(user_id=1, balance=1000, plan=PlanType.PRO)

    async def get_wallet(self, user_id: int):
        return self.wallet

    async def update_balance(self, user_id: int, new_balance: int):
        # Имитируем сбой диска или СУБД
        raise OSError("Сбой дисковой подсистемы базы данных при записи!")

    async def record_transaction(
        self, user_id, amount, transaction_id, status, partner_metadata=None
    ):
        return True

    async def get_transaction(self, transaction_id: str):
        return None

    async def list_transactions(self, user_id: int):
        return []


@pytest.mark.asyncio
async def test_billing_service_handles_db_failure_gracefully():
    """Тест: при сбое репозитория сервис не оставляет данные в рассинхроне."""
    service = BillingService(repo=FaultyMockRepo())

    with pytest.raises(IOError) as exc_info:
        await service.charge_click(
            user_id=1, link_id=10, amount=50, transaction_id="tx_faulty_test_001"
        )

    assert "Сбой дисковой подсистемы" in str(exc_info.value)


@pytest.mark.asyncio
async def test_stripe_transaction_id_does_not_expose_token_prefix() -> None:
    token = "tok_secret_12345678"

    transaction_id = await StripePaymentGateway("api-key").process_external_charge(token, 100)

    assert token[:8] not in transaction_id
    assert transaction_id == "ch_stripe_f22e725e_100"
