# app\enums\user_enums.py
from enum import Enum


class UserRole(str, Enum):
    super_admin = "super_admin"
    cemetery_admin = "cemetery_admin"
    staff = "staff"