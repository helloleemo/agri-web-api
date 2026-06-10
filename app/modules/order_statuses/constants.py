from enum import IntEnum


class OrderStatusCode(IntEnum):
    ORDER_CREATED = 1
    ORDER_CONFIRMED = 2
    PENDING_PAYMENT = 3
    PAID = 4
    PREPARING = 5
    SHIPPING = 6
