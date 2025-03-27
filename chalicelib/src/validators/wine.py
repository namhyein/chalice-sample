import logging
from typing import Dict, List, Optional

from pydantic import AliasChoices, BaseModel, Field

from chalicelib.setting import DOMAIN
from chalicelib.src.tools.processor import PriceProcessor
from chalicelib.src.utils import make_slug, replace_to_multi_language
from chalicelib.src.validators.field import (Element, FullImage, MarketPrice,
                                             Price, Score, Thumbnail,
                                             ThumbnailElement)
from chalicelib.static.image import STANDARD_GLASS_IMAGE
from chalicelib.static.wine import (AROMA_DESCRIPTION, DECANT_ICON, DECANT_MAP,
                                    GRAPE_DESCRIPTION, PAIRING_DESCRIPTION,
                                    SERVE_ICON, SERVE_MAP)


class TasteChart(BaseModel):
    name: str
    score: int
    description: str 
        
        
class TasteStructure(BaseModel):
    body: Optional[TasteChart] = Field(default=None)
    tannin: Optional[TasteChart] = Field(default=None)
    acidity: Optional[TasteChart] = Field(default=None)
    sweetness: Optional[TasteChart] = Field(default=None)

    
class Vote(BaseModel):
    id: str
    name: str
    count: int
    

class TotalCriticReview(BaseModel):
    reviewCount: int = Field(gt=0)
    actualScore: Score
    predictedScore: Score
    actualVotes: List[Vote] = Field(default_factory=list)
    predictedVotes: List[Vote] = Field(default_factory=list)
    tasteStructure: TasteStructure = Field(default_factory=TasteStructure)
    description: Optional[str] = Field(default=None)
    colors: List[str] = Field(default_factory=list)
    aromas: List[str] = Field(default_factory=list)
    palates: List[str] = Field(default_factory=list)
    pairings: List[str] = Field(default_factory=list)
    ingredients: List[str] = Field(default_factory=list)
    

class CriticProfile(BaseModel):
    id: str
    name: str
    thumbnail: Thumbnail
    organization: str
    description: Optional[str] = Field(default=None)

    

class DetailCriticReview(BaseModel):
    note: str
    profile: CriticProfile
    isPredicted: bool
    actualScore: Score
    predictedScore: Score
    actualQuality: Optional[Element] = Field(default=None)
    predictedQuality: Optional[Element] = Field(default=None)
    href: Optional[str] = Field(default=None)
    tastedAt: Optional[str] = Field(default=None)
    tasteStructure: TasteStructure = Field(default_factory=TasteStructure)
    colors: List[str] = Field(default_factory=list)
    aromas: List[str] = Field(default_factory=list)
    palates: List[str] = Field(default_factory=list)
    pairings: List[str] = Field(default_factory=list)
    ingredients: List[str] = Field(default_factory=list)


class CriticReview(BaseModel):
    total: TotalCriticReview
    detailItem: Dict[str, DetailCriticReview] = Field(default_factory=dict)
    detailTypes: List[ThumbnailElement] = Field(default_factory=list)
    

class HistoryPriceOption(BaseModel):
    timestamp: int
    globalAvgValue: Optional[float] = Field(default=None)
    localAvgValue: Optional[float] = Field(default=None)
    


class HistoryPrice(BaseModel):
    option1: List[HistoryPriceOption] = Field(default_factory=list)
    option2: List[HistoryPriceOption] = Field(default_factory=list)
    option3: List[HistoryPriceOption] = Field(default_factory=list)
    description: Optional[str] = Field(default=None)
    

class GlobalPrice(BaseModel):
    value: float
    currency: str
    symbol: str
    country: str


class Vintage(BaseModel):
    year: str
    href: Optional[str] = Field(default=None, pattern="/.*")
    critic: Score = Field(default_factory=Score)
    user: Score = Field(default_factory=Score)
       


class WineHighlight(BaseModel):
    value: str
    icon: Thumbnail
    

class WineRegion(BaseModel):
    name: str
    thumbnail: Thumbnail
    id: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    
    
class Wine(BaseModel):
    id: str
    name: str
    vintage: str
    
    @staticmethod
    def convert_wine_name(name: str, winery: str, vintage: str) -> str:
        wine_name_slug = make_slug(name)
        winery_id = make_slug(winery) if winery else ""
        
        if winery_id not in wine_name_slug:
            name = f"{winery.strip()} {name.strip()}"
        if vintage.lower() not in wine_name_slug:
            name = f"{name.strip()} {vintage.strip()}"
        return name.strip()
    
    @staticmethod
    def make_canonical(slug: str, vintage: str, is_default: bool) -> str:
        if is_default:
            return f"{DOMAIN}/wine/{slug}"
        return f"{DOMAIN}/wine/{slug}?vintage={vintage}"
    
    @staticmethod
    def make_href(slug: str, vintage: str, is_default: bool) -> str:
        if is_default:
            return f"/wine/{slug}"
        return f"/wine/{slug}?vintage={vintage}"
    
    @staticmethod
    def make_critic_score(score: Dict[str, dict]) -> Score:
        result = Score(ground=100)
        
        if not score:
            return result
        
        score_values = []
        for value in score.values():
            if not value.get("value") or not value.get("ground"):
                continue
            if value["ground"] != 5:
                score_value = value["value"] * (100 / value["ground"])
                score_values.append(score_value)
        
        if score_values:
            result.value = int(sum(score_values) / len(score_values))
            result.value = round(result.value, 1)
        
        print(result.value)
        return result
    
    
class WineCard(Wine):
    href: str = Field(pattern="/.*")
    price: str
    thumbnail: Thumbnail
    alcohol: Optional[float] = Field(default=None)
    types: List[str] = Field(default_factory=list)
    criticScore: Optional[Score] = Field(default=None)
    country: Optional[str] = Field(default=None)
    region: Optional[str] = Field(default=None)
    winery: Optional[str] = Field(default=None)
    highlight: Optional[str] = Field(default=None)
        
    @staticmethod
    def to_items(items: List[dict], language: str, location: str):
        card_items = []
        for item in items:
            name = item["name"]
            href = Wine.make_href(slug=item["slug"], vintage=item["vintage"], is_default=item.get("is_default", False))
            types = [type["name"].upper() for type in item["types"]]
            region = item["region"].get("name") if item.get("region") else None
            country = item["country"].get("name") if item.get("country") else None
            winery = item["winery"].get("name") if item.get("winery") else None
            
            if language in ["ko", "ja"]:
                # name = item.get(language, {}).get("name") or name
                region = item.get(language, {}).get("region", {}).get("name")
                country = item.get(language, {}).get("country", {}).get("name")
                winery = item.get(language, {}).get("winery", {}).get("name")
                types = [type["name"].upper() for type in item.get(language, {}).get("types", [])] or types
                href = f"/{language}" + href
            
            card_items.append(
                WineCard(
                    id=item["_id"],
                    href=href,
                    name=Wine.convert_wine_name(name, winery, item["vintage"]),
                    types=types,
                    price=PriceProcessor().make_price_string(location=location, price=item.get("global_market_price")),
                    region=region,
                    winery=winery,
                    country=country,
                    vintage=item["vintage"],
                    alcohol=item["alcohol"],
                    thumbnail=item["image"]["thumbnail"],
                    highlight=item.get("highlight"),
                    criticScore=Wine.make_critic_score(item.get("score"))
                )
            )
        return card_items     


class Decant(BaseModel):
    icon: Thumbnail = Field(default=Thumbnail(**DECANT_ICON["short"]))
    hours: Optional[float] = Field(default=None)
    description: Optional[str] = Field(default=None)
    
    @staticmethod
    def to_item(name: str, vintage: str, language: str, types: List[str], sweetness: Optional[float], body: Optional[float]):
        selected_item, selected_type = None, None
        for _type in types:
            if _type in DECANT_MAP.keys():
                selected_type = _type
                selected_item = DECANT_MAP[_type]
                break
        
        if not selected_item:
            return Decant()
        
        if (
            selected_type == "red"
            and vintage >= "2018"
        ):
            selected_item = DECANT_MAP["red_young"]
        elif (
            selected_type == "white"
            and sweetness and sweetness <= 2
        ):
            selected_item = DECANT_MAP["white_dry"]
        elif (
            selected_type == "white"
            and body and body <= 2
        ):
            selected_item = DECANT_MAP["white_light"]
        
        return Decant(
            icon=selected_item["icon"],
            hours=selected_item["hours"],
            description=selected_item["description"][language].format(name=name)
        )
        

class Serve(BaseModel):
    icon: Thumbnail = Field(default=Thumbnail(**SERVE_ICON["cool"]))
    temperature: str = Field(default="-")
    
    
    @staticmethod
    def to_item(
        vintage: str, 
        types: List[str], 
        sweetness: Optional[float], 
        body: Optional[float],
        language: str
    ):
        selected_item, selected_type = None, None
        for _type in types:
            if _type in SERVE_MAP.keys():
                selected_type = _type
                selected_item = SERVE_MAP[_type]
                break
        
        if not selected_item:
            return Serve()
        
        if (
            selected_type == "red"
            and vintage >= "2018"
        ):
            selected_item = SERVE_MAP["red_young"]
        elif (
            selected_type == "white"
            and sweetness and sweetness <= 2
        ):
            selected_item = SERVE_MAP["white_dry"]
        elif (
            selected_type == "white"
            and body and body <= 2
        ):
            selected_item = SERVE_MAP["white_light"]
        
        min_temperature = selected_item["temperature"]["min"]
        max_temperature = selected_item["temperature"]["max"]
        temperature_unit = selected_item["temperature"]["unit"]
        if language != "en":
            min_temperature = (min_temperature - 32) * 5 / 9
            max_temperature = (max_temperature - 32) * 5 / 9
            temperature_unit = "°C" 
            
        temperature = f"{int(min_temperature)}-{int(max_temperature)}{temperature_unit}"
        
        return Serve(
            icon=selected_item["icon"],
            temperature=temperature
        )
        
class Aroma(BaseModel):
    primary: List[Element] = Field(default_factory=list)
    secondary: List[Element] = Field(default_factory=list)
    tertiary: List[Element] = Field(default_factory=list)
    description: Optional[str] = Field(default=None)
    
    @staticmethod
    def to_item(name: str, aroma: Optional[dict], language: str):
        item = Aroma()
        
        if not aroma:
            return item
        
        item.primary = [Element(**element) for element in aroma.get("primary", [])]
        item.secondary = [Element(**element) for element in aroma.get("secondary", [])]
        item.tertiary = [Element(**element) for element in aroma.get("tertiary", [])]
        
        # description
        primary_map = Aroma.make_map(aroma.get("primary", []), language=language)
        secondary_map = Aroma.make_map(aroma.get("secondary", []), language=language)
        tertiary_map = Aroma.make_map(aroma.get("tertiary", []), language=language)
        
        if primary_map:
            primary_map = sorted(primary_map.items(), key=lambda x: len(x[1]), reverse=True)
            primary_category, primary_items = primary_map[0]
        else:
            primary_category, primary_items = None, []
        
        if secondary_map:
            secondary_map = sorted(secondary_map.items(), key=lambda x: len(x[1]), reverse=True)
            secondary_category, secondary_items = secondary_map[0]
        else:
            secondary_category, secondary_items = None, []
            
        if tertiary_map:
            tertiary_map = sorted(tertiary_map.items(), key=lambda x: len(x[1]), reverse=True)
            tertiary_category, tertiary_items = tertiary_map[0]
        else:
            tertiary_category, tertiary_items = None, []
        
        if aroma.get("description"):
            item.description = aroma["description"]
        else:
            if primary_category and secondary_category and tertiary_category:
                item.description = AROMA_DESCRIPTION["all"][language].format(
                    name=name,
                    primary_items=", ".join(primary_items[:3]),
                    primary_category=primary_category,
                    secondary_items=", ".join(secondary_items[:3]),
                    secondary_category=secondary_category,
                    tertiary_items=", ".join(tertiary_items[:3]),
                )
            elif primary_category and secondary_category:
                item.description = AROMA_DESCRIPTION["double_secondary"][language].format(
                    name=name,
                    primary_items=", ".join(primary_items[:3]),
                    primary_category=primary_category,
                    secondary_items=", ".join(secondary_items[:3]),
                    secondary_category=secondary_category
                )
            elif primary_category and tertiary_category:
                item.description = AROMA_DESCRIPTION["double_tertiary"][language].format(
                    name=name,
                    primary_items=", ".join(primary_items[:3]),
                    primary_category=primary_category,
                    tertiary_items=", ".join(tertiary_items[:3]),
                    tertiary_category=tertiary_category
                )
            elif primary_category:
                item.description = AROMA_DESCRIPTION["single"][language].format(
                    name=name,
                    primary_items=", ".join([a.name for a in item.primary[:5]]),
                )
                
        return item
        
    @staticmethod
    def make_map(aromas: List[dict], language: str):
        item_map = {}
        
        for aroma in aromas:
            group_name = aroma.get("group", {}).get("name")
            if not group_name or group_name.lower() == "other":
                continue
            
            group_name = aroma.get(language, {}).get("group", {}).get("name")
            if not group_name:
                continue
            
            group_name = group_name.strip("\b").strip()
            if group_name and group_name not in item_map:
                item_map[group_name] = []
            else:
                continue
            
            item_map[group_name].append(aroma["name"])
        return item_map


class GrapeElement(BaseModel):
    id: Optional[str] = Field(default=None)
    name: str
    percent: Optional[float] = Field(default=None)
    

class Grape(BaseModel):
    primary: Optional[GrapeElement] = Field(default=None)
    secondary: Optional[GrapeElement] = Field(default=None)
    tertiary: List[GrapeElement] = Field(default_factory=list)
    description: Optional[str] = Field(default=None)
    
    @staticmethod
    def to_item(name: str, grape: Optional[dict], language: str):
        item = Grape()
        
        if not grape or not grape.get("items"):
            return item
        
        grape_items = grape.get("items", [])
        grape_details = grape.get("details", [])
        
        percent_map = {
            item["name"]: item.get("percent") for item in grape_items
        }
        items = [
            GrapeElement(
                id=elem["_id"],
                name=elem["name"] if language == "en" else elem[language]["name"],
                percent=percent_map[elem["name"]]
            ) for elem in grape_details if elem["name"] and elem.get("ko", {}).get("name") and elem.get("ja", {}).get("name")
        ]
        try:
            items = sorted(items, key=lambda x: x.percent, reverse=True)
        except TypeError:
            logging.info("TypeError: Grape percent is None type")
            pass
            
        # primaryItem, secondaryItem, tertiaryItems
        item.primary = items[0] if items else None
        item.secondary = items[1] if len(items) > 1 else None
        item.tertiary = items[2:] if len(items) > 2 else []

        # description
        if len(items) == 1:
            item.description = GRAPE_DESCRIPTION["single"][language].format(name=name, grape_names=items[0].name)
        elif len(items) > 1:        
            try:
                grapes_with_percent = [f"{item['name']}-{item['percent']}%" for item in items]
                grapes_with_percent = ", ".join(grapes_with_percent)
                
                primary_grape_name = items[0]["name"]
                else_grapes = [item["name"] for item in items[1:]]
                
                if len(else_grapes) == 1:
                    else_grape_names = else_grapes[0]
                else:
                    else_grape_names = ", ".join(else_grape_names[:-1]) + f" and {else_grape_names[-1]}"
                
                item.description = GRAPE_DESCRIPTION["multiple_percent"][language].format(name=name,
                                                                                          primary_grape_name=primary_grape_name,
                                                                                          else_grape_names=else_grape_names,
                                                                                          grapes_with_percent=grapes_with_percent)
            except:
                grape_names = [item.name for item in items]
                grape_names = ", ".join(grape_names)
                item.description = GRAPE_DESCRIPTION["multiple"][language].format(name=name, grape_names=grape_names)
            
        return item


class Glass(BaseModel):
    id: str = Field(default="standard", validation_alias=AliasChoices("id", "_id"))
    name: str = Field(default="Standard")
    icon: Thumbnail = Field(default=Thumbnail(**STANDARD_GLASS_IMAGE))
    
    @staticmethod
    def to_item(glass: Optional[dict]):
        try:
            if isinstance(glass, list):
                glass = glass[0]
            
            return Glass(
                **{
                    **glass,
                    "name": glass["name"].title(),
                    "icon": glass["image"]["icon"]
                }
            )
        except:
            return Glass()

       
class PairingElement(BaseModel):
    id: Optional[str] = Field(default=None, validation_alias=AliasChoices("id", "_id"))
    name: str
    items: List[Element] = Field(default_factory=list)
    thumbnail: Optional[Thumbnail] = Field(default=None)
    description: Optional[str] = Field(default=None)


class Pairing(BaseModel):
    items: List[PairingElement] = Field(default_factory=list)
    description: Optional[str] = Field(default=None)
    
    
    @staticmethod
    def to_item(name: str, language: str, pairing: Optional[dict]):
        item = Pairing()
        
        if not pairing:
            return item

        item_ids = []
        for elem in pairing.get("items", []):
            elem_id = make_slug(elem["name"])
            if elem_id in item_ids:
                continue
            item.items.append(PairingElement(**elem))
            
        if item.items:
            pairing_names = [elem.name for elem in item.items]
            pairing_names = ", ".join(pairing_names)
            item.description = PAIRING_DESCRIPTION[language].format(name=name, pairing_items=pairing_names)
        
        return item 


class WineDetail(Wine):
    slug: str
    image: FullImage
    glassType: Element
    decantIcon: Thumbnail
    serveIcon: Thumbnail
    glassIcon: Thumbnail
    description: Optional[str] = Field(default=None)
    infoDescription: Optional[str] = Field(default=None)
    alcohol: Optional[float] = Field(default=None)
    country: Optional[Element] = Field(default=None)
    region: Optional[WineRegion] = Field(default=None)
    winery: Optional[WineRegion] = Field(default=None)
    vineyard: Optional[WineRegion] = Field(default=None)
    types: List[Element] = Field(default_factory=list)
    highlights: List[WineHighlight] = Field(default_factory=list)
    userScore: Optional[Score] = Field(default=None)
    criticScore: Optional[Score] = Field(default=None)
    vintages : List[Vintage] = Field(default_factory=list)
    tasteStructure: TasteStructure = Field(default_factory=TasteStructure)
    
    # grape
    grapeDescription: Optional[str] = Field(default=None)
    primaryGrape: Optional[GrapeElement] = Field(default=None)
    secondaryGrape: Optional[GrapeElement] = Field(default=None)
    tertiaryGrapes: List[GrapeElement] = Field(default_factory=list)
    
    # aroma
    aromaDescription: Optional[str] = Field(default=None)
    primaryAromas: List[Element] = Field(default_factory=list)
    secondaryAromas: List[Element] = Field(default_factory=list)
    tertiaryAromas: List[Element] = Field(default_factory=list)
    
    # pairing
    pairingDescription: Optional[str] = Field(default=None)
    pairingItems: List[PairingElement] = Field(default_factory=list)
    
    # technical
    technicalDescription: Optional[str] = Field(default=None)
    phLevel: Optional[str] = Field(default=None)
    dosage: Optional[str] = Field(default=None)
    residualSugar: Optional[str] = Field(default=None)
    totalAcidity: Optional[str] = Field(default=None)
    volatileAcidity: Optional[str] = Field(default=None)
    freeSO2: Optional[str] = Field(default=None)
    totalSO2: Optional[str] = Field(default=None)
    dryExtract: Optional[str] = Field(default=None)
    
    # winemaking
    firstVintage: Optional[str] = Field(default=None)
    production: Optional[str] = Field(default=None)
    closure: Optional[str] = Field(default=None)
    wineMakers: List[str] = Field(default_factory=list)
    ageingLength: Optional[str] = Field(default=None)
    ageingContainer: Optional[str] = Field(default=None)
    bottlingLength: Optional[str] = Field(default=None)
    fermentationLength: Optional[str] = Field(default=None)
    malolacticFermentation: Optional[str] = Field(default=None)
    alcoholicFermentationLength: Optional[str] = Field(default=None)
    macerationTechnique: Optional[str] = Field(default=None)
    macerationLength: Optional[str] = Field(default=None)
    
    # vineyard technical
    farmingSystem: Optional[str] = Field(default=None)
    harvestDate: Optional[str] = Field(default=None)
    harvestMethod: Optional[str] = Field(default=None)
    vineDensity: Optional[str] = Field(default=None)
    vineYield: Optional[str] = Field(default=None)
    altitude: Optional[str] = Field(default=None)
    exposure: Optional[str] = Field(default=None)
    soilComposition: Optional[str] = Field(default=None)
    vineAge: Optional[str] = Field(default=None)
    
    # decant
    decantDescription: Optional[str] = Field(default=None)
    decantHours: Optional[float] = Field(default=None)
    serveTemperature: Optional[str] = Field(default=None)
    
    # price
    priceDescription: Optional[str] = Field(default=None)
    actualPrice: Optional[Price] = Field(default=None)
    predictedPrice: Optional[Price] = Field(default=None)
    currentMarketPrices: List[MarketPrice] = Field(default_factory=list)
    historyPrice: Optional[HistoryPrice] = Field(default=None)
    globalPriceDescription: Optional[str] = Field(default=None)
    globalPrices: List[GlobalPrice] = Field(default_factory=list)
    
    criticReview: Optional[CriticReview] = Field(default=None)
    
    @staticmethod
    def to_item(location: str, language: str, document: dict):
        name = Wine.convert_wine_name(document["name"], document["winery"]["name"], document["vintage"])
        glass = Glass.to_item(glass=document.get("glass_type"))