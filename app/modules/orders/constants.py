from enum import IntEnum


class PaymentMethodCode(IntEnum):
    BANK_TRANSFER = 1
    FACE_TO_FACE = 2
    LINE_PAY = 3

    @classmethod
    def label(cls, code: int) -> str:
        labels = {
            cls.BANK_TRANSFER.value: "匯款",
            cls.FACE_TO_FACE.value: "面交",
            cls.LINE_PAY.value: "linepay",
        }
        return labels.get(code, "")


class DeliveryMethodCode(IntEnum):
    HOME_DELIVERY = 1
    OTHER = 2

    @classmethod
    def label(cls, code: int) -> str:
        labels = {
            cls.HOME_DELIVERY.value: "宅配",
            cls.OTHER.value: "其他",
        }
        return labels.get(code, "")