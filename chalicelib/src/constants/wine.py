from enum import Enum


class REVIEW_QUALITY(Enum):
    QTY_EXTRAORDINARY = "extraordinary"
    QTY_OUTSTANDING = "outstanding"
    QTY_GOOD = "good"
    QTY_AVERAGE = "average"
    QTY_NOT_RECOMMENDED = "not-recommended"
    QTY_UNACCEPTABLE = "unacceptable"
    
    @staticmethod
    def __member_values__():
        return REVIEW_QUALITY._value2member_map_.keys()
    
    @staticmethod
    def to_name(value: str):
        return value.replace("-", " ").title()