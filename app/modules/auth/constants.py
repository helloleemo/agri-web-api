from enum import Enum


class AuthEmailTemplateType(Enum):
    REGISTRATION_VERIFICATION = 1
    PASSWORD_RESET = 2

    @property
    def display_name(self) -> str:
        names = {
            self.REGISTRATION_VERIFICATION: "註冊驗證信",
            self.PASSWORD_RESET: "密碼重置信",
        }
        return names.get(self, "未知類型")
