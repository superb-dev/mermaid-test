import uuid

import pydantic

# TODO: Comments


# Shared properties
class Wallet(pydantic.BaseModel):
    id: str
    balance: pydantic.constr(min_length=1, regex=r"\d+", strict=True)


# Properties to receive via API on creation
class WalletCreate(pydantic.BaseModel):
    user_id: uuid.UUID


# Properties to receive via API on update
class WalletAmountWithNonce(pydantic.BaseModel):
    amount: pydantic.constr(min_length=1, regex=r"\d+", strict=True)
    nonce: pydantic.constr(min_length=8, max_length=16)

    @property
    def int_amount(self) -> int:
        return int(self.amount)

    @pydantic.validator("amount")
    def amount_is_positive(cls, v):
        if int(v) <= 0:
            raise ValueError("amount should be a positive integer")


class WalletDeposit(WalletAmountWithNonce):
    pass


class WalletTransfer(WalletAmountWithNonce):
    pass
