WINE_DETAIL_PROJECTION = {
    "_id": 1,
    "slug": 1,
    "name": 1,
    "vintage": 1,
    "image.thumbnail": 1,
    "glass_type": 1,
    "decant": 1,
    "serve": 1,
    "description": 1,
    "alcohol": 1,
    "country": 1,
    "region": 1,
    "winery": 1,
    "vineyard": 1,
    "types": 1,
    "highlights": 1,
    "vintages": 1,
    "score": 1,
    "statistic": 1,
    "grape": 1,
    "pairing": 1,
    "aroma": 1,
    "winemaking": 1,
    "taste": 1,
    "global_history_price": 1,
    "global_market_price": 1,
    "vestimated_price": 1,
    "meta": 1,
    "created_at": 1,
    "updated_at": 1,
    "ko": 1,
    "ja": 1,
    "is_default": 1,
    "critic_score": 1
}

WINE_LIST_PROJECTION = {
    "_id": 1,
    "slug": 1,
    "name": 1,
    "vintage": 1,
    "global_market_price": 1,
    "is_default": 1,
    "image.thumbnail": 1,
    "alcohol": 1,
    "types": 1,
    "score": 1,
    "country.name": 1,
    "region.name": 1,
    "winery.name": 1,
}

WINE_REDIRECT_PROJECTION = {
    "_id": 1,
    "slug": 1,
    "vintage": 1,
    "is_default": 1,
}

JOIN_GLASS_PROJECTION = {
    "_id": 1,
    "name": 1,
    "image.icon": 1,
}
JOIN_COUNTRY_PROJECTION = {
    "_id": 1,
    "name": 1,
    "ko.name": 1,
    "ja.name": 1,
}
JOIN_REGION_PROJECTION = {
    "_id": 1,
    "name": 1,
    "summary": 1,
    "image.thumbnail": 1,
    "ko.name": 1,
    "ja.name": 1,
    "ko.summary": 1,
    "ja.summary": 1,
}
JOIN_WINERY_PROJECTION = {
    "_id": 1,
    "name": 1,
    "summary": 1,
    "image.thumbnail": 1,
    "ko.name": 1,
    "ja.name": 1,
    "ko.summary": 1,
    "ja.summary": 1,
}
JOIN_PAIRING_PROJECTION = {
    "_id": 1,
    "image.thumbnail": 1,
    "ko.name": 1,
    "ja.name": 1,
}
JOIN_AROMA_PROJECTION = {
    "_id": 1,
    "name": 1,
    "image.thumbnail": 1,
    "group.name": 1,
    "ko.group.name": 1,
    "ja.group.name": 1,
    "ko.name": 1,
    "ja.name": 1,
}
JOIN_TYPE_PROJECTION = {
    "_id": 1,
    "name": 1,
    "ko.name": 1,
    "ja.name": 1,
}
JOIN_GRAPE_PROJECTION = {
    "_id": 1,
    "name": 1,
    "ko.name": 1,
    "ja.name": 1,
}
JOIN_VINTAGE_PROJECTION = {
    "_id": 1,
    "slug": 1,
    "vintage": 1,
    "filter.score": 1,
    "is_default": 1
}

JOIN_REVIEW_PROJECTION = {
    "_id": 0,
    "critic": 1,
    "score": 1,
    "taste_structure": 1,
    "keyword": 1,
    "published_at": 1,
    "tasted_at": 1,
    "note": 1,
    "is_predicted": 1,
    "quality": 1,
    "source.url": 1,
    "ko": 1,
    "ja": 1,
}
JOIN_CRITIC_PROJECTION = {
    "_id": 1,
    "name": 1,
    "image.profile": 1,
    "ko.name": 1,
    "ja.name": 1,
    "organization.name": 1,
    "description": 1,
    "ko.description": 1,
    "ja.description": 1,
}