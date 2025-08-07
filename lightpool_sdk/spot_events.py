from dataclasses import dataclass
from typing import Optional
from .types import ObjectID, Address

@dataclass
class OrderCreatedEvent:
    order_id: ObjectID
    side: int  # 0 for Buy, 1 for Sell
    amount: int
    creator: Address
    order_type: int  # 0 for Limit, 1 for Market, 2 for Trigger
