from enum import Enum


class COLLECTION(Enum):
    TYPE = "types"
    WINE = "wines"
    USER = "users"
    TOKEN = "tokens"
    AROMA = "aromas"
    GRAPE = "grapes"
    GLASS = "glasses"
    REGION = "regions"
    CRITIC = "critics"
    EDITOR = "editors"
    MODULE = "modules"
    WINERY = "wineries"
    COMMENT = "comments"
    ARTICLE = "articles"
    PAIRING = "pairings"
    COUNTRY = "countries"
    CATEGORY = "categories"
    CURRENCY = "currencies"
    INTERACTION = "interactions"
    SUBSCRIPTION = "subscriptions"
    CRITIC_REVIEW = "critic_reviews"
    
    @staticmethod
    def __member_values__():
        return COLLECTION._value2member_map_.keys()


class PLATFORM(Enum):
    GOOGLE = "google"
    
    @staticmethod
    def __member_values__():
        return list(PLATFORM._value2member_map_.keys())


class ITEM_TYPE(Enum):
    FAQ = "faq"
    WINE = "wine"
    WINERY = "winery"
    EDITOR = "editor"
    REGION = "region"
    ARTICLE = "article"
    COMMENT = "comment"
    
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
    
    
class HOME_MODULE_KEY(Enum):
    WINE_PICK = "wine-pick"
    RECENT_NEWS = "recent-news"
    RECENT_FEATURE = "recent-feature"
    RECENT_CULTURE = "recent-culture"
    RECENT_RANKING = "recent-ranking"
    RECENT_KNOWLEDGE = "recent-knowledge"
    
    CRITIC_ARTICLE_1 = "critic-article-1"
    CRITIC_ARTICLE_2 = "critic-article-2"
    CRITIC_WINE_1 = "critic-wine-1"
    CRITIC_WINE_2 = "critic-wine-2"
    
    MD_PICK_ARTICLE_1 = "md-pick-article-1"
    MD_PICK_ARTICLE_2 = "md-pick-article-2"
    MD_PICK_WINE_1 = "md-pick-wine-1"
    MD_PICK_WINE_2 = "md-pick-wine-2"

    @staticmethod
    def __member_values__():
        return list(HOME_MODULE_KEY._value2member_map_.keys())
    