from enum import Enum


class CustomizedEnum(Enum):
    
    @staticmethod
    def __member_values__():
        return list(CustomizedEnum._value2member_map_.keys())