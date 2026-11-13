"""Shared Pydantic helpers."""

from decimal import Decimal
from typing import Annotated

from pydantic import PlainSerializer

# Business logic and persistence use Decimal. API responses expose numbers for
# charting convenience; precision-critical calculations never use float.
Money = Annotated[
    Decimal,
    PlainSerializer(lambda value: float(value), return_type=float, when_used="json"),
]
Percent = Annotated[
    Decimal,
    PlainSerializer(lambda value: float(value), return_type=float, when_used="json"),
]
