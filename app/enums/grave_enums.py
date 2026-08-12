from enum import Enum


class IdentificationType(str, Enum):
    cnic = "cnic"
    passport = "passport"
    nicop = "nicop"
    other = "other"