from enum import Enum

class UserTier(Enum):
    FREE = "free"
    PRO = "pro"

class UserStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"
    SUSPENDED = "suspended"  # Added suspended status
    DELETED = "deleted"  