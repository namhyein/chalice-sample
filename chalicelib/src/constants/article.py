from enum import Enum

from chalicelib.static.article import ARTICLE_CATEGORY_MAP


class BLOCK_TYPE(Enum):
    H1 = "heading_1"
    H2 = "heading_2"
    H3 = "heading_3"
    IMAGE = "image"
    PARAGRAH = "paragraph"
    BULLET_LIST = "bulleted_list_item"
    NUMBERED_LIST = "numbered_list_item"
    
    @staticmethod
    def __member_values__():
        return BLOCK_TYPE._value2member_map_.keys()
    
    
class ARTICLE_CATEGORY(Enum):
    NEWS = "news"
    FEATURE = "feature"
    CULTURE = "culture"
    RANKING = "ranking"
    KNOWLEDGE = "knowledge"
    
    @staticmethod
    def __member_values__():
        return ARTICLE_CATEGORY._value2member_map_.keys()
    
    @staticmethod
    def translate(value: str, language: str):
        return ARTICLE_CATEGORY_MAP[value][language] if value in ARTICLE_CATEGORY_MAP else value
    

class ARTICLE_MODULE_KEY(Enum):
    # MAIN
    RECENT = "recent"
    MD_PICK_1 = "md-pick-1"
    MD_PICK_2 = "md-pick-2"
    MAIN_PICK = "main-pick"
    MOST_READ = "most-read"
    TODAY_PICK = "today-pick"
    CATEGORY_PICK = "category-pick"
    
    # LIST
    FAQ = "faq"
    TOP_MAIN = "top_main"
    MODULE_1 = "module_1"
    MODULE_2 = "module_2"
    
    # DETAIL
    READ_MORE = "read_more"
    
    @staticmethod
    def __member_values__():
        return list(ARTICLE_MODULE_KEY._value2member_map_.keys())