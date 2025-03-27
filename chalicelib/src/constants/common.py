from enum import Enum


class COLLECTION(Enum):
    WINE = "wines"
    USER = "users"
    
    @staticmethod
    def __member_values__():
        return COLLECTION._value2member_map_.keys()


class PLATFORM(Enum):
    GOOGLE = "google"
    
    @staticmethod
    def __member_values__():
        return list(PLATFORM._value2member_map_.keys())


class ITEM_TYPE(Enum):
    WINE = "wine"
    WINERY = "winery"
    REGION = "region"
    
    @staticmethod
    def __member_values__():
        return ITEM_TYPE._value2member_map_.keys()
    

class REACTION(Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    BOOKMARK = "bookmark"
    
    @staticmethod
    def __member_values__():
        return REACTION._value2member_map_.keys()


class STATUS(Enum):
    PUBLISHED = 1
    DELETED = -3
    
    @staticmethod
    def __member_values__():
        return STATUS._value2member_map_.keys()