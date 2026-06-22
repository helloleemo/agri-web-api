from enum import StrEnum


class InventoryLedgerAction(StrEnum):
    INITIALIZE = "INITIALIZE"
    RESERVE = "RESERVE"
    RELEASE = "RELEASE"
    COMMIT_DEDUCT = "COMMIT_DEDUCT"
    MANUAL_ADJUST = "MANUAL_ADJUST"
