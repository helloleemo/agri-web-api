from enum import IntEnum


class OrderStatusCode(IntEnum):
    ORDER_CREATED = 1
    ORDER_CONFIRMED_AND_PENDING_PAYMENT = 2
    PAID_AND_PREPARING = 3
    SHIPPING = 4
    DELIVERED = 5
    CANCELED = 6
    REFUNDED = 7
    OTHER = 99