from http import HTTPStatus
from typing import Any, Dict, List, Optional, Tuple

from chalicelib.setting import DOMAIN
from chalicelib.src.constants.common import (COLLECTION, ITEM_TYPE, REACTION,
                                             STATUS)
from chalicelib.src.constants.wine import REVIEW_QUALITY
from chalicelib.src.tools.database import mongodb_obj
from chalicelib.src.tools.processor import PriceProcessor
from chalicelib.src.utils import (convert_date_to_string,
                                  convert_timestamp_to_string,
                                  decrease_days_to_timestamp,
                                  get_now_timestamp)
from chalicelib.src.validators.field import (SEO, AdditionalMeta, Breadcrumb,
                                             Element, FullImage, Languages,
                                             MarketPrice, Meta, MetaData,
                                             Price, Score, Thumbnail,
                                             ThumbnailElement)
from chalicelib.src.validators.response import (DefaultResponse,
                                                RedirectResponse)
from chalicelib.src.validators.wine import (Aroma, CriticProfile, CriticReview,
                                            Decant, DetailCriticReview, Glass,
                                            GlobalPrice, Grape, HistoryPrice,
                                            HistoryPriceOption, Pairing, Serve,
                                            TasteChart, TasteStructure,
                                            TotalCriticReview, Vintage, Vote,
                                            Wine, WineDetail, WineHighlight,
                                            WineRegion)
from chalicelib.static.image import (BULB_ICON, REGION_DEFAULT_IMAGE,
                                     VIVINO_ICON, WALLET_ICON, WINE_ICON,
                                     WINERY_DEFAULT_IMAGE)
from chalicelib.static.wine import (COST_EFFECTIVENESS, CRITIC_DESCRIPTION,
                                    DECANT_ICON, ESTIMATED_PRICE_DESCRIPTION,
                                    GLOBAL_PRICE_DESCRIPTION, INFO_DESCRIPTION,
                                    PRICE_DESCRIPTION, SERVE_ICON,
                                    TECHNICAL_DESCRIPTION)

from .constant import *
from .request import (GetWineDetailRequest, GetWineReactionRequest,
                      WineReactionRequest)
from .response import GetWineDetailResponse, GetWineReactionResponse


class WineService(PriceProcessor):
    
    def get_item(self, input: GetWineDetailRequest) -> Tuple[GetWineDetailResponse, HTTPStatus]:
        """
            와인 상세 정보 조회
        """
        
        if document := self._fetch_data_detail(id=input.id):
            return self._handle_response_detail(location=input.location,
                                                language=input.language,
                                                document=document), HTTPStatus.OK
            
        ## DB NOT FOUND
        query = {
            "status": {
                "$gte": STATUS.PUBLISHED.value
            },
            "is_default": True
        }
        if not self.check_if_id_is_slug(input.id):
            # _id로 찾을 수 없다면 slug로 찾아보기
            words = input.id.split("-")
            slug = "-".join(words[:-1])
            query["_id"] = {"$regex": slug}
        else:
            # slug로도 찾을 수 없으면 redirection 여부 체크
            query["redirections"] = {"$in": [input.id]}            
        
        if document := mongodb_obj.get_document(
            query=query,
            collection=COLLECTION.WINE.value,
            projection=WINE_REDIRECT_PROJECTION
        ):
            redirect = RedirectResponse.make_redirect_url(f"/wine/{document['slug']}", input.language)
            return RedirectResponse(redirect=redirect), HTTPStatus.MOVED_PERMANENTLY
        
        redirect = RedirectResponse.make_redirect_url(f"/wine", input.language)
        message = f"wine not found: {input.id}"
        return RedirectResponse(redirect=redirect, message=message), HTTPStatus.NOT_FOUND
    
    def update_reaction(self, input: WineReactionRequest) -> Tuple[DefaultResponse, HTTPStatus]:
        """
            와인 리액션 (좋아요, 싫어요, 북마크)
        """
        
        query = {
            "user": input.user, 
            "item": input.id,
            "item_type": ITEM_TYPE.WINE.value
        }
        if input.action == REACTION.LIKE:
            update = {
                "like": {
                    "$cond": {
                        "if": {"$ne": ["$like", 1]},
                        "then": 1,
                        "else": 0
                    }
                }
            }
        elif input.action == REACTION.DISLIKE:
            update = {
                "like": {
                    "$cond": {
                        "if": {"$ne": ["$like", -1]},
                        "then": -1,
                        "else": 0
                    }
                }
            }
        elif input.action == REACTION.BOOKMARK:
            update = {
                "bookmark": {
                    "$cond": {
                        "if": {"$ne": ["$bookmark", 1]},
                        "then": 1,
                        "else": 0
                    }
                }
            }
        
        mongodb_obj.upsert_document(
            query=query,
            update_query=[{"$set": update}],
            collection=COLLECTION.INTERACTION.value)
        return DefaultResponse(status=HTTPStatus.OK), HTTPStatus.OK
    
    def get_reaction(self, input: GetWineReactionRequest) -> Tuple[GetWineReactionResponse, HTTPStatus]:
        """
            와인 리액션 조회
        """
        
        # update article
        query = {
            "user": input.user,
            "item": input.id,
            "item_type": "wine"
        }
        projection = {
            "_id": 0,
            "like": 1,
            "bookmark": 1
        }
        if document := mongodb_obj.get_document(
            query=query,
            projection=projection,
            collection=COLLECTION.INTERACTION.value,
        ):
            like = document.get("like") == 1
            dislike = document.get("like") == -1
            bookmark = document.get("bookmark") == 1
        else:
            like = False
            dislike = False
            bookmark = False
            
        return GetWineReactionResponse(
                like=like,
                dislike=dislike,
                bookmark=bookmark,
                status=HTTPStatus.OK
            ), HTTPStatus.OK       
        
    ###############################
    # METHODS for Business Logic
    ###############################
    def _fetch_data_detail(self, id: str) -> Optional[dict]:
        """
            MongoDB에서 ID에 해당하는 와인 상세 정보 조회
            - ID가 실제 _id일 수도 있고, slug일 수도 있음
        """
        
        # query = {"status": {"$gte": STATUS.PUBLISHED.value}}
        query = {}
        if not self.check_if_id_is_slug(id):
            query.update({"_id": id})
        else:
            query.update({
                "_id": {"$regex": id},
                "slug": id,
                "is_default": True,
                "status": {"$ne": STATUS.DELETED.value}
            })
            
        join_glass = self._make_lookup_query(
            collection=COLLECTION.GLASS,
            local_field="glass_type._id",
            as_field="glass_type",
            required_fields=[key for key, value in JOIN_GLASS_PROJECTION.items() if value]
        )
        join_country = self._make_lookup_query(
            collection=COLLECTION.COUNTRY,
            local_field="country._id",
            as_field="country",
            required_fields=[key for key, value in JOIN_COUNTRY_PROJECTION.items() if value]
        )
        join_region = self._make_lookup_query(
            collection=COLLECTION.REGION,
            local_field="region._id",
            as_field="region",
            required_fields=[key for key, value in JOIN_REGION_PROJECTION.items() if value]
        )
        join_pairing = self._make_lookup_query(
            collection=COLLECTION.PAIRING,
            local_field="pairing.items._id",
            as_field="pairing_items",
            required_fields=[key for key, value in JOIN_PAIRING_PROJECTION.items() if value]
        )
        join_primary_aroma = self._make_lookup_query(
            collection=COLLECTION.AROMA,
            local_field="aroma.primary._id",
            as_field="aroma.primary",
            required_fields=[key for key, value in JOIN_AROMA_PROJECTION.items() if value]
        )
        join_secondary_aroma = self._make_lookup_query(
            collection=COLLECTION.AROMA,
            local_field="aroma.secondary._id",
            as_field="aroma.secondary",
            required_fields=[key for key, value in JOIN_AROMA_PROJECTION.items() if value]
        )
        join_tertiary_aroma = self._make_lookup_query(
            collection=COLLECTION.AROMA,
            local_field="aroma.tertiary._id",
            as_field="aroma.tertiary",
            required_fields=[key for key, value in JOIN_AROMA_PROJECTION.items() if value]
        )
        join_types = self._make_lookup_query(
            collection=COLLECTION.TYPE,
            local_field="types._id",
            as_field="types",
            required_fields=[key for key, value in JOIN_TYPE_PROJECTION.items() if value]
        )
        join_grape = self._make_lookup_query(
            collection=COLLECTION.GRAPE,
            local_field="grape.items._id",
            as_field="grape.details",
            required_fields=[key for key, value in JOIN_GRAPE_PROJECTION.items() if value],
        )
        join_vintages = self._make_lookup_query(
            collection=COLLECTION.WINE,
            local_field="slug",
            foreign_field="slug",
            required_fields=[key for key, value in JOIN_VINTAGE_PROJECTION.items() if value],
            as_field="available_vintages",
        )
        join_recommended_wine = self._make_lookup_query(
            collection=COLLECTION.WINE,
            local_field="module.recommended_wine.items._id",
            as_field="module.recommended_wine.items",
            required_fields=[key for key, value in WINE_LIST_PROJECTION.items() if value],
        )
        join_reviews = {
            "from": COLLECTION.CRITIC_REVIEW.value,
            "localField": "_id",
            "foreignField": "wine._id",
            "as": "critic_reviews",
            "pipeline": [
                {
                    "$match": {
                        "status": {"$in": [STATUS.PUBLISHED.value, -9201]}
                    }    
                },
                {
                    "$project": JOIN_REVIEW_PROJECTION
                },
                {
                    "$lookup": {
                        "from": COLLECTION.CRITIC.value,
                        "localField": "critic._id",
                        "foreignField": "_id",
                        "as": "critic",
                        "pipeline": [
                            {
                                "$match": {
                                    "status": {"$gte": STATUS.PUBLISHED.value}
                                }  
                            },
                            {
                                "$project": JOIN_CRITIC_PROJECTION
                            }
                        ]
                    }
                }
            ]
        }
        pipelines = [
            {"$match": query},
            {"$limit": 1},
            {"$project": WINE_DETAIL_PROJECTION},
            {"$lookup": join_vintages},
            {"$lookup": join_pairing},
            {"$lookup": join_country},
            {"$lookup": join_reviews},
            {"$lookup": join_region},
            {"$lookup": join_grape},
            {"$lookup": join_glass},
            {"$lookup": join_types},
            {"$lookup": join_primary_aroma},
            {"$lookup": join_secondary_aroma},
            {"$lookup": join_tertiary_aroma},
            {"$lookup": join_recommended_wine},
        ]
        
        # OK
        if documents := mongodb_obj.aggregate_documents(
            collection=COLLECTION.WINE.value,
            pipelines=pipelines
        ):
            return documents[0]
        return None
        
    def _handle_response_detail(self, 
                                location: str,
                                language: str,
                                document: Dict[str, Any]) -> GetWineDetailResponse:
        # MULTI LANGUAGE        
        if language != "en":
            document = self._replace_to_multi_language(document, language)
        
        winery = self._normalize_winery(document["winery"], language)
        
        document["name"] = Wine.convert_wine_name(name=document["name"],
                                                  winery=winery.name if winery else "",
                                                  vintage=document["vintage"])
       
        region = self._normalize_region(document["region"], language)
        country = self._normalize_country(document["country"], language)        

        types = [Element(**{**item, "name": item["name"].upper()}) for item in document.get("types", [])]
        glass = Glass.to_item(glass=document["glass_type"][0] if document.get("glass_type") else None)
        grape = Grape.to_item(name=document["name"], grape=document.get("grape"), language=language)
        aroma = Aroma.to_item(name=document["name"], aroma=document.get("aroma"), language=language)     
        pairing = Pairing.to_item(name=document["name"], language=language, pairing=document.get("pairing"))
        
        history_price = self._normalize_history_price(location=location, history_price=document.get("global_history_price"))
        global_prices = self._normalize_global_prices(location=location, market_price=document.get("global_market_price"))
        local_prices = self._normalize_local_prices(location=location, market_price=document.get("global_market_price"))
        actual_price = self._normalize_actual_price(local_prices=local_prices)
        predicted_price = self._normalize_estimated_price(location=location, vestimated_price=document.get("vestimated_price"))

        price_for_value = self._calculate_price_for_value(
            source=predicted_price,
            target=actual_price
        )
        cost_effective = self._calculate_cost_effectiveness(price_for_value=price_for_value)
        global_price_description = self._normalize_global_price_description(
            name=document["name"],
            location=location,
            language=language,
            global_prices=global_prices,
            price_for_value=price_for_value
        )
        price_description = self._normalize_price_description(
            name=document["name"],
            location=location,
            language=language,
            cost_effective=cost_effective,
        )
        highlights = self._normalize_highlights(
            highlights=document["highlights"], 
            score=document.get("score"), 
            cost_effective=cost_effective,
            language=language
        )        

    
        critic_score = Wine.make_critic_score(document.get("score"))
        critic_review = self._normalize_critic_review(name=document["name"], language=language, critic_reviews=document["critic_reviews"])

        taste_structure = self._normalize_taste(taste=document["taste"], language=language)
        technical_description = document.get("winemaking", {}).get("description") or TECHNICAL_DESCRIPTION[language].format(name=document["name"])
        
        href = Wine.make_href(slug=document["slug"], vintage=document["vintage"], is_default=document["is_default"])
        canonical = self._make_detail_canonical(
            slug=document["slug"], 
            vintage=document["vintage"],
            is_default=document["is_default"]
        )
        languages = Languages.to_item(canonical)
        canonical = languages.ko if language == "ko" else languages.ja if language == "ja" else languages.en
                
        vintages = self._normalize_vintages(document["vintages"], document["available_vintages"])     
        thumbnail = FullImage(**{
            **document["image"]["thumbnail"],
            "alt": f"{document['name']} thumbnail"  
        })
        
        if document.get("serve") and document["serve"].get("temperature"):
            min = document["serve"]["temperature"]["min"]
            max = document["serve"]["temperature"]["max"]
            unit = document["serve"]["temperature"]["unit"]
            
            if language != "en":
                min = (min - 32) * 5 / 9
                max = (max - 32) * 5 / 9
                unit = "°C"
            
            key = "cool" if min < 44 else "medium" if min < 55 else "hot"
            icon = SERVE_ICON[key]
            temp = f"{int(min)}-{int(max)}{unit}"
            
            serve = Serve(icon=Thumbnail(**icon), temperature=temp)
        else:
            serve = Serve.to_item(vintage=document["vintage"],
                                  types=[_type["_id"] for _type in document.get("types")],
                                  body=document["taste"]["structure"].get("body"),
                                  sweetness=document["taste"]["structure"].get("sweetness"),
                                  language=language)
        
        if decant := document.get("decant"):
            hour = decant.get("hours") or 0
            
            key = "short" if hour < 1 else "medium" if hour < 2 else "long"
            icon = DECANT_ICON[key]
            description = (
                decant.get("description") if language == "en"
                else document[language].get("decant", {}).get("description")
            )
            decant = Decant(icon=Thumbnail(**icon),
                            hours=hour,
                            description=description)
        else:
            decant = Decant.to_item(name=document["name"],
                                    types=[_type["_id"] for _type in document.get("types")],
                                    vintage=document["vintage"],
                                    language=language,
                                    body=document["taste"]["structure"].get("body"),
                                    sweetness=document["taste"]["structure"].get("sweetness"))
        
        item = WineDetail(
            id=document["_id"],
            slug=document["slug"],
            name=document["name"],
            types=types,
            image=thumbnail,
            vintages=vintages,
            highlights=highlights,
            criticScore=critic_score,
            vintage=document["vintage"],
            alcohol=document.get("alcohol"),
            description=document.get("description"),
            
            winery=winery,
            region=region,
            country=country,
            
            glassIcon=glass.icon,
            glassType=Element(name=glass.name, id=glass.id),
            decantIcon=decant.icon,
            decantHours=decant.hours,
            decantDescription=decant.description,
            serveIcon=serve.icon,
            serveTemperature=serve.temperature,
            
            primaryGrape=grape.primary,
            secondaryGrape=grape.secondary,
            tertiaryGrapes=grape.tertiary,
            grapeDescription=grape.description,
            
            primaryAromas=aroma.primary,
            secondaryAromas=aroma.secondary,
            tertiaryAromas=aroma.tertiary,
            aromaDescription=aroma.description,
            
            pairingItems=pairing.items,
            pairingDescription=pairing.description,
            
            historyPrice=history_price,
            priceDescription=price_description,
            currentMarketPrices=local_prices,
            globalPrices=global_prices,
            globalPriceDescription=global_price_description,
            actualPrice=actual_price,
            predictedPrice=predicted_price,
            
            criticReview=critic_review,

            tasteStructure=taste_structure,
            technicalDescription=technical_description,
            firstVintage=document["winemaking"].get("first_vintage") or None,
            production=document["winemaking"].get("production") or None,
            closure=document["winemaking"].get("closure") or None,
            wineMakers=document["winemaking"].get("wine_makers", []),
            phLevel=document["taste"]["technical"].get("ph_level") or None,
            dosage=document["taste"]["technical"].get("dosage") or None,
            dryExtract=document["taste"]["technical"].get("dry_extract") or None,
            totalAcidity=document["taste"]["technical"].get("total_acidity") or None,
            volatileAcidity=document["taste"]["technical"].get("volatile_acidity") or None,
            freeSO2=document["taste"]["technical"].get("free_so2") or None,
            totalSO2=document["taste"]["technical"].get("total_so2") or None,
            residualSugar=document["taste"]["technical"].get("residual_sugar") or None,
        )
        item.infoDescription = self._normalize_info_description(item=item, language=language)
        
        return GetWineDetailResponse(
            metaData=MetaData(
                location=location,
                language=language,  
            ),
            seo=SEO(
                meta=self._make_detail_meta(document=document),
                datePublished=convert_timestamp_to_string(timestamp=document["created_at"], _format="%Y-%m-%d"),
                dateModified=convert_timestamp_to_string(timestamp=document["updated_at"], _format="%Y-%m-%d"),
                breadcrumbs=[
                    Breadcrumb(
                        href="/",
                        name="Home"
                    ),
                    Breadcrumb(
                        href=f"/wine",
                        name="Wine"
                    ),
                    Breadcrumb(
                        href=href,
                        name=document["name"]
                    )
                ],
                image=thumbnail,
                canonical=canonical,
                addtionalMeta=AdditionalMeta(languages=languages)
            ),
            item=item,
            module={},
        )
      
    ##############################################################
    # FIELD NORMALIZERS
    ##############################################################
    def _normalize_info_description(self, item: WineDetail, language: str) -> str:
        description = ""
        
        optional_descriptions = INFO_DESCRIPTION["options"][language]
        if (
            item.name 
            and item.region 
            and item.region.name 
            and item.country 
            and item.country.name
            and item.primaryGrape
        ):
            grape_items = [item.primaryGrape]
            if item.secondaryGrape:
                grape_items.append(item.secondaryGrape)
            if item.tertiaryGrapes:
                grape_items.extend(item.tertiaryGrapes)
                
            grape_names = ", ".join([grape_item.name for grape_item in grape_items])
            description += optional_descriptions[0].format(
                name=item.name, 
                grape_names=grape_names.title(), 
                region=item.region.name.title(), 
                country=item.country.name.title(), 
            )
        if (
            item.types
            and item.decantHours is not None
            and item.serveTemperature
        ):
            description += " " + optional_descriptions[1].format(
                name=item.name,
                type=" ".join([_type.name for _type in item.types]).title(),
                decant_hours=item.decantHours,
                serve_temperature=item.serveTemperature
            )
        if (
            item.primaryAromas
            and (
                item.tasteStructure.body
                or item.tasteStructure.acidity
                or item.tasteStructure.tannin
                or item.tasteStructure.sweetness
            )
        ):
            aroma_items = [elem.name for elem in item.primaryAromas] + [elem.name for elem in item.secondaryAromas] + [elem.name for elem in item.tertiaryAromas]
            aroma_items = list(set(aroma_items))[:5]
            aroma_names = ", ".join(aroma_items)
            
            taste_keywords = []
            if item.tasteStructure.body:
                taste_keywords.append(item.tasteStructure.body.name)
            if item.tasteStructure.acidity:
                taste_keywords.append(item.tasteStructure.acidity.name)
            if item.tasteStructure.tannin:
                taste_keywords.append(item.tasteStructure.tannin.name)
            if item.tasteStructure.sweetness:
                taste_keywords.append(item.tasteStructure.sweetness.name)
            
            description += " " + optional_descriptions[2].format(
                name=item.name, 
                aromas=aroma_names.title(), 
                taste_keywords=", ".join(taste_keywords).title(), 
            )
        
        if not description:
            description = INFO_DESCRIPTION["default"][language]
        return description.strip()
    
    def _normalize_winery(self, winery: dict, language: str) -> Optional[WineRegion]:    
        
        if (
            not winery 
            or not isinstance(winery, dict)
            or not winery.get("name")
        ):
            return None
        
        thumbnail = winery.get("image", {}).get("thumbnail")
        if not thumbnail or not thumbnail.get("url"):
            thumbnail = WINERY_DEFAULT_IMAGE
            
        return WineRegion(
            name=winery["name"],
            description=winery.get("description"),
            thumbnail=Thumbnail(**thumbnail)
        )
        
    def _normalize_region(self, region: List[dict], language: str) -> Optional[WineRegion]:    
        
        if (
            not region 
            or not isinstance(region, list)
            or not region[0].get("name")
        ):
            return None
        
        region = region[0]
        
        # name
        name = region["name"] if language == "en" else region[language]["name"]
        
        # thumbnail => 이미지 리사이즈 에러남.. 일단 전부 기본 이미지로 대체
        # if thumbnail := region["image"].get("thumbnail"):
        #     thumbnail = Thumbnail(**{
        #         **thumbnail,
        #         "alt": f"{name} Image"
        #     })
        # else: 
        thumbnail = Thumbnail(**{
            **REGION_DEFAULT_IMAGE,
            "alt": f"{name} Image"
        })
        
        # description
        summary = region["summary"] if language == "en" else region[language]["summary"]
        
        return WineRegion(
            name=name,
            # id=region["_id"],
            description=summary,
            thumbnail=thumbnail
        )
        
    def _normalize_country(self, country: List[dict], language: str) -> Optional[Element]:
        if (
            not country 
            or not isinstance(country, list)
            or not country[0].get("name")
        ):
            return None
        
        country = country[0]
        name = country["name"] if language == "en" else country[language]["name"]
        return Element(
            name=name, 
            # id=country["_id"]
        )
        
        
    def _normalize_highlights(
        self, 
        highlights: List[str], 
        score: Dict[str, Any],
        cost_effective: Optional[int],
        language: str
    ) -> List[WineHighlight]:
        
        results = []
        
        if highlights:
            results.append(
                WineHighlight(
                    value=highlights[0],
                    icon=Thumbnail(**BULB_ICON)
                )
            )
            
        user_score, critic_score = None, None
        if score:
            for spider, rating in score.items():
                if not rating.get("value"):
                    continue
                
                if spider in ["vivino", "wine-searcher"]:
                    user_score = WineHighlight(
                        value=f"{spider.title()} {rating['value']:.1f}/5.0",
                        icon=Thumbnail(**VIVINO_ICON)
                    )
                elif spider in ["robertparker", "jamessuckling", "vinous"]:
                    critic_name = (
                        "Robert Parker" if spider == "robertparker" 
                        else "James Suckling" if spider == "jamessuckling" 
                        else spider.title()
                    )
                    critic_score = WineHighlight(
                        value=f"{int(rating['value'])} By {critic_name}",
                        icon=Thumbnail(**WINE_ICON)
                    )
                    
        if user_score:
            results.append(user_score)
        
        if isinstance(cost_effective, int):
            results.append(
                WineHighlight(
                    value=(
                        COST_EFFECTIVENESS["high"][language] if cost_effective == 1
                        else COST_EFFECTIVENESS["average"][language] if cost_effective == 0
                        else COST_EFFECTIVENESS["low"][language]
                    ),
                    icon=Thumbnail(**WALLET_ICON)
                )
            )    
        if critic_score:
            results.append(critic_score)        
        return results
    
    def _normalize_taste(self, taste: dict, language: str) -> TasteStructure:        
        return TasteStructure(
            body=self._check_taste_body(taste["structure"].get("body"), language),
            acidity=self._check_taste_acidity(taste["structure"].get("acidity"), language),
            tannin=self._check_taste_tannin(taste["structure"].get("tannin"), language),
            sweetness=self._check_taste_sweetness(taste["structure"].get("sweetness"), language),
        )
        
    def _normalize_vintages(self, all_vintages: List[str], vintages: List[dict]) -> List[Vintage]:
        results = []
        vintage_map = {vintage["vintage"]: vintage for vintage in vintages}
        
        for vintage in all_vintages:
            if vintage in vintage_map:
                results.append(
                    Vintage(
                        year=vintage_map[vintage]["vintage"],
                        href=Wine.make_href(
                            slug=vintage_map[vintage]["slug"], 
                            vintage=vintage_map[vintage]["vintage"],
                            is_default=vintage_map[vintage]["is_default"]
                        ),
                        critic=Wine.make_critic_score(vintage_map[vintage].get("score")),
                        user=Score(ground=5) 
                    )
                )
            else:
                results.append(
                    Vintage(
                        year=vintage,
                        critic=Score(ground=100),
                        user=Score(ground=5)
                    )
                )
        return results
    
    def _normalize_estimated_price(self, location: str, vestimated_price: dict) -> Optional[Price]:
        if not vestimated_price or not vestimated_price.get("value"):
            return None
        
        _, currency = self._check_country_and_currency(location)
        
        if currency == "USD":
            return Price(
                value=round(vestimated_price["value"], 1),
                currency=currency,
                symbol=self.currency_map[currency]["symbol"]
            )
        
        price_value = self._to_currency(
            currency=currency,
            price=vestimated_price["value"],
        )
        return Price(
            value=round(price_value, 1),
            currency=currency,
            symbol=self.currency_map[currency]["symbol"]
        )
    
    def _normalize_local_prices(self, location: str, market_price: dict) -> List[MarketPrice]:
        return self.select_local_prices(location=location, price=market_price)

    def _normalize_actual_price(self, local_prices: List[MarketPrice]) -> Optional[Price]:
        if not local_prices:
            return None
        
        minimum_value = self.get_minimum_price(prices=local_prices)
        return Price(
            value=round(minimum_value, 1),
            symbol=local_prices[0].symbol,
            currency=local_prices[0].currency
        )
    
    def _normalize_history_price(self, location: str, history_price: dict) -> Optional[HistoryPrice]:
        """
            price: {
                united-states: {
                    references: [
                        {
                            name: "Wine-Searcher",
                            url: "https://www.wine-searcher.com",
                        }
                    ],
                    items: [
                        {
                            timestamp: 1698796800,
                            currency: "USD",
                            value: 100.0
                        }
                    ] 
                }
            }
        """
        if not history_price:
            return None
        
        local_country, currency = self._check_country_and_currency(location)
        
        # timestamp에 대하여 전체 가격 합 / 지역 별 가격 구하기
        price_per_timestamp = {}
        for country, price_info in history_price.items():        
            for price in price_info["items"]:
                timestamp = price["timestamp"]
                price_value = self._convert_price_value(currency=currency, price=price)

                if timestamp not in price_per_timestamp:
                    price_per_timestamp[timestamp] = {"total": 0, "count": 0, "local": 0}
                    
                price_per_timestamp[timestamp]["total"] += price_value
                price_per_timestamp[timestamp]["count"] += 1

                if country == local_country:
                    price_per_timestamp[timestamp]["local"] = price_value

        # timestamp에 대하여 전체 평균 가격 / 지역 별 평균 가격 구하기
        all_history_prices = [
            HistoryPriceOption(
                timestamp=int(timestamp),
                globalAvgValue=round(value["total"] / value["count"], 1),
                localAvgValue=value["local"] if country else round(value["total"] / value["count"], 1)
            ) for timestamp, value in price_per_timestamp.items()
        ]
                
        option_1 = [] # 6개월 이내의 가격만 가져오기
        option_2 = [] # 12개월 이내의 가격만 가져오기 + 2개월 간격으로 평균값 계산
        option_3 = [] # 24개월 이내의 가격만 가져오기 + 4개월 간격으로 평균값 계산
        
        option_1_timestamp = decrease_days_to_timestamp(
            timestamp=get_now_timestamp(), days=6*30
        )
        option_2_timestamp = decrease_days_to_timestamp(
            timestamp=get_now_timestamp(), days=12*30
        )
        option_3_timestamp = decrease_days_to_timestamp(
            timestamp=get_now_timestamp(), days=24*30
        )
        
        all_history_prices.reverse()
    
        for idx, price in enumerate(all_history_prices):
            if price.timestamp >= option_1_timestamp:
                option_1.append(
                    HistoryPriceOption(
                        timestamp=price.timestamp,
                        globalAvgValue=price.globalAvgValue,
                        localAvgValue=price.localAvgValue if price.localAvgValue else None
                    )
                )
            
            if idx and idx % 1 == 0 and price.timestamp >= option_2_timestamp:
                global_avg = sum([price.globalAvgValue for price in all_history_prices[idx-2:idx]])/2
                local_avg = sum([price.localAvgValue for price in all_history_prices[idx-2:idx]])/2
                
                price = HistoryPriceOption(
                    timestamp=price.timestamp,
                    globalAvgValue=round(global_avg, 1) if global_avg else None,
                    localAvgValue=round(local_avg, 1) if local_avg else None
                )
                if price.globalAvgValue or price.localAvgValue:
                    option_2.append(price)
            
            if idx and idx % 3 == 0 and price.timestamp >= option_3_timestamp:
                global_avg = sum([price.globalAvgValue for price in all_history_prices[idx-4:idx]])/4
                local_avg = sum([price.localAvgValue for price in all_history_prices[idx-4:idx]])/4
                
                price = HistoryPriceOption(
                    timestamp=price.timestamp,
                    globalAvgValue=round(global_avg, 1) if global_avg else None,
                    localAvgValue=round(local_avg, 1) if local_avg else None
                )
                if price.globalAvgValue or price.localAvgValue:
                    option_3.append(price)
        
        option_1.reverse()
        option_2.reverse()
        option_3.reverse()
        return HistoryPrice(
            option1=option_1,
            option2=option_2,
            option3=option_3
        )
        
    def _normalize_global_prices(self, location: str, market_price: Optional[dict]) -> List[GlobalPrice]:
        if not market_price:
            return []
        
        _, currency = self._check_country_and_currency(location)
        
        # global price
        global_prices: List[GlobalPrice] = []
        
        # 국가별 평균 가격들
        for country, prices in market_price.items():
            if country not in self.country_map:
                continue
            
            market_prices = []
            for price in prices:
                try:
                    market_prices.append(
                        self.convert_to_market_price(
                            country=country,
                            currency=currency,
                            price=price
                        )
                    )
                except:
                    continue

            average_price = self.get_average_price(prices=market_prices)
            global_prices.append(
                GlobalPrice(
                    value=average_price,
                    currency=currency,
                    symbol=self.currency_map[currency]["symbol"],
                    country=self.country_map[country]["alpha_2"]
                )
            )
        
        # 낮은 가격 순으로 정렬
        global_prices = sorted(global_prices, key=lambda x: x.value)
        
        ## 국가가 하나밖에 없는 경우 global price를 띄우지 않음
        return global_prices if len(global_prices) > 1 else []
    
    def _normalize_global_price_description(
        self, 
        name: str,
        location: str,
        language: str, 
        price_for_value: Optional[float],
        global_prices: List[GlobalPrice],
    ) -> Optional[str]:
        if not global_prices:
            return None
        
        local = None
        for price in global_prices:
            if price.country == location:
                local = price
                break
        local_price = f"{local.symbol}{local.value}" if local else None
        local_country = self.country_map[location] 
        
        lowest = global_prices[0]
        lowest_price = f"{lowest.symbol}{lowest.value}"
        lowest_country = self.country_map[lowest.country]
        
        if not local:
            description = GLOBAL_PRICE_DESCRIPTION["default"][language].format(
                name=name,
                lowest_price=lowest_price,
                lowest_country=lowest_country["name"],
            )
            return description
        elif lowest_country["_id"] == local_country["_id"]:
            description = GLOBAL_PRICE_DESCRIPTION["cheap"][language].format(
                name=name,
                local_price=lowest_price,
                local_country=local_country["name"],
            )
            if price_for_value and price_for_value >= 0.2:
                description += " " + ESTIMATED_PRICE_DESCRIPTION["ineffective"][language].format(
                    name=name,
                    percent=price_for_value,
                    local_country=local_country,
                )
            return description
        else:
            description = GLOBAL_PRICE_DESCRIPTION["expensive"][language].format(
                name=name,
                local_price=local_price,
                local_country=local_country["name"],
                lowest_price=lowest_price,
                lowest_country=lowest_country["name"],
            )
            if price_for_value is not None and price_for_value <= 0:
                description += " " + ESTIMATED_PRICE_DESCRIPTION["effective"][language].format(
                    name=name,
                    local_country=local_country,
                )    
            return description

    def _normalize_price_description(self, name: str, location: str, language: str, cost_effective: Optional[int]) -> Optional[str]:
        if not cost_effective:
            return PRICE_DESCRIPTION["default"][language].format(name=name)
        
        local_country = self.country_map[location]["name"]
        if cost_effective == 1:
            return PRICE_DESCRIPTION["high"][language].format(name=name, local_country=local_country)
        elif cost_effective == 0:
            return PRICE_DESCRIPTION["average"][language].format(name=name, local_country=local_country)
        else:
            return PRICE_DESCRIPTION["low"][language].format(name=name, local_country=local_country)

    def _normalize_critic_review(self, name: str, critic_reviews: List[dict], language: str) -> Optional[CriticReview]:
        if not critic_reviews or not isinstance(critic_reviews, list):
            return None
        
        total_actual_score = 0
        total_actual_count = 0
        total_predicted_score = 0
        total_predicted_count = 0
        
        total_actual_vote = {key: 0 for key in REVIEW_QUALITY.__member_values__()}
        total_predicted_vote = {key: 0 for key in REVIEW_QUALITY.__member_values__()}
        
        total_aroma = {}
        total_color = {}
        total_palate = {}
        total_pairing = {}
        total_ingredient = {}
        
        total_body = 0
        total_body_count = 0
        total_acidity = 0
        total_acidity_count = 0
        total_tannin = 0
        total_tannin_count = 0
        total_sweetness = 0
        total_sweetness_count = 0
        
        review_detail = {}
        review_detail_types = []
        for detail in critic_reviews:
            if not detail.get("critic"):
                continue
            
            critic = detail["critic"][0]
            
            critic_id = critic["_id"]
            actual_score = self._make_100_point_score(detail["score"]["actual"]["value"], detail["score"]["actual"]["ground"])
            predicted_score = self._make_100_point_score(detail["score"]["predicted"]["value"], detail["score"]["predicted"]["ground"])
            if actual_score:
                total_actual_score += actual_score
                total_actual_count += 1
            if predicted_score:
                total_predicted_score += predicted_score
                total_predicted_count += 1
                
            actual_quality_id = detail["quality"]["actual"]["_id"]
            predicted_quality_id = detail["quality"]["predicted"]["_id"]
            
            if not actual_quality_id or not predicted_quality_id:
                continue
            
            if actual_quality_id in total_actual_vote:
                total_actual_vote[actual_quality_id] += 1
            
            if predicted_quality_id in total_predicted_vote:
                total_predicted_vote[predicted_quality_id] += 1
                
            for aroma in detail["keyword"]["aromas"]:
                aroma = aroma.replace("_", " ")
                if aroma not in total_aroma:
                    total_aroma[aroma] = 0
                total_aroma[aroma] += 1
                
            for color in detail["keyword"]["colors"]:
                color = color.replace("_", " ")
                if color not in total_color:
                    total_color[color] = 0
                total_color[color] += 1
                
            for palate in detail["keyword"]["palates"]:
                palate = palate.replace("_", " ")
                if palate not in total_palate:
                    total_palate[palate] = 0
                total_palate[palate] += 1
                
            for pairing in detail["keyword"]["pairings"]:
                pairing = pairing.replace("_", " ")
                if pairing not in total_pairing:
                    total_pairing[pairing] = 0
                total_pairing[pairing] += 1
                
            for ingredient in detail["keyword"]["ingredients"]:
                ingredient = ingredient.replace("_", " ")
                if ingredient not in total_ingredient:
                    total_ingredient[ingredient] = 0
                total_ingredient[ingredient] += 1
            
            taste_structure = TasteStructure(
                body=self._check_taste_body(detail["taste_structure"]["body"], language),
                acidity=self._check_taste_acidity(detail["taste_structure"]["acidity"], language),
                tannin=self._check_taste_tannin(detail["taste_structure"]["tannin"], language),
                sweetness=self._check_taste_sweetness(detail["taste_structure"]["sweetness"], language),
            )
            if taste_structure.body and taste_structure.body.score: 
                total_body += taste_structure.body.score
                total_body_count += 1
            if taste_structure.acidity and taste_structure.acidity.score: 
                total_acidity += taste_structure.acidity.score
                total_acidity_count += 1
            if taste_structure.tannin and taste_structure.tannin.score: 
                total_tannin += taste_structure.tannin.score
                total_tannin_count += 1
            if taste_structure.sweetness and taste_structure.sweetness.score: 
                total_sweetness += taste_structure.sweetness.score
                total_sweetness_count += 1

            review_detail[critic_id] = DetailCriticReview(
                profile=CriticProfile(
                    name=critic["name"],
                    id=critic["_id"],
                    description=critic["description"],
                    thumbnail=Thumbnail(**critic["image"]["profile"]),
                    organization=critic["organization"]["name"],
                ),
                href=detail["source"]["url"],
                note=detail["note"]["actual"] if detail["note"].get("actual") else detail["note"]["predicted"],
                isPredicted=detail["is_predicted"],
                actualScore=Score(
                    value=detail["score"]["actual"]["value"],
                    ground=detail["score"]["actual"]["ground"]
                ),
                predictedScore=Score(
                    value=detail["score"]["predicted"]["value"],
                    ground=detail["score"]["predicted"]["ground"]
                ),
                actualQuality=self._check_quality(actual_quality_id),
                predictedQuality=self._check_quality(predicted_quality_id),
                tasteStructure=taste_structure,
                tastedAt=(
                    convert_date_to_string(detail["tasted_at"], _format="%b %d, %Y") if detail.get("tasted_at")
                    else convert_date_to_string(detail["published_at"], _format="%b %d, %Y") if detail.get("pubilshed_at")
                    else None
                ),
                colors=detail["keyword"]["colors"][:5],
                aromas=detail["keyword"]["aromas"][:5],
                palates=detail["keyword"]["palates"][:5],
                pairings=detail["keyword"]["pairings"][:5],
                ingredients=detail["keyword"]["ingredients"][:5],
            )
        
        review_detail_types = [
            ThumbnailElement(
                id=critic_id,
                name=critic.profile.name,
                thumbnail=critic.profile.thumbnail,
            ) for critic_id, critic in review_detail.items()   
        ]
        
        total_colors = sorted(total_color.items(), key=lambda x: x[1], reverse=True)
        total_aromas = sorted(total_aroma.items(), key=lambda x: x[1], reverse=True)
        total_palates = sorted(total_palate.items(), key=lambda x: x[1], reverse=True)
        total_pairings = sorted(total_pairing.items(), key=lambda x: x[1], reverse=True)
        total_ingredients = sorted(total_ingredient.items(), key=lambda x: x[1], reverse=True)
        
        total_colors = [color[0] for color in total_colors]
        total_aromas = [aroma[0] for aroma in total_aromas]
        total_palates = [palate[0] for palate in total_palates]
        total_pairings = [pairing[0] for pairing in total_pairings]
        total_ingredients = [ingredient[0] for ingredient in total_ingredients]
        
        total_body = (total_body / total_body_count) if total_body_count else None
        total_acidity = (total_acidity / total_acidity_count) if total_acidity_count else None
        total_tannin = (total_tannin / total_tannin_count) if total_tannin_count else None
        total_sweetness = (total_sweetness / total_sweetness_count) if total_sweetness_count else None
        
        tastes = []
        if total_body:
            tastes.append(self._check_taste_body(total_body, language))
        if total_acidity:
            tastes.append(self._check_taste_acidity(total_acidity, language))
        if total_tannin:
            tastes.append(self._check_taste_tannin(total_tannin, language))
        if total_sweetness:
            tastes.append(self._check_taste_sweetness(total_sweetness, language))    
            
        total_actual_score = (total_actual_score / total_actual_count) if total_actual_count else None
        total_predicted_score = (total_predicted_score / total_predicted_count) if total_predicted_count else None
        
        # description
        colors = [color.title() for color in total_colors]
        colors = ", ".join(colors)[:2]
        aromas = [aroma.title() for aroma in total_aromas]
        aromas = ", ".join(aromas)[:3]
        palates = [palate.title() for palate in total_palates]
        palates = ", ".join(palates)[:3]
        pairings = [pairing.title() for pairing in total_pairings]
        pairings = ", ".join(pairings)[:3]
        
        if total_actual_score >= 90:
            if colors and aromas and palates and pairings:
                description = CRITIC_DESCRIPTION["high"][language].format(
                    name=name,
                    color=colors,
                    aromas=aromas,
                    taste=palates,
                    pairing=pairings,
                    rating=int(total_actual_score)
                )
            else:
                description = CRITIC_DESCRIPTION["default_high"][language].format(
                    name=name,
                    rating=int(total_actual_score)
                )
            
        elif total_actual_score >= 80:
            if colors and aromas and palates and pairings:
                description = CRITIC_DESCRIPTION["average"][language].format(
                    name=name,
                    color=colors,
                    aromas=aromas,
                    taste=palates,
                    pairing=pairings,
                    rating=int(total_actual_score)
                )
            else:
                description = CRITIC_DESCRIPTION["default_average"][language].format(
                    name=name,
                    rating=int(total_actual_score)
                )
        else:
            if colors and aromas and palates and pairings:
                description = CRITIC_DESCRIPTION["low"][language].format(
                    name=name,
                    color=colors,
                    aromas=aromas,
                    taste=palates,
                    pairing=pairings,
                    rating=int(total_actual_score)
                )
            else:
                description = CRITIC_DESCRIPTION["default_low"][language].format(
                    name=name,
                    rating=int(total_actual_score)
                )
            
        return CriticReview(
            detailItem=review_detail,
            detailTypes=review_detail_types,
            total=TotalCriticReview(
                description=description,
                reviewCount=len(review_detail_types),
                actualScore=Score(value=round(total_actual_score, 1), ground=100),
                predictedScore=Score(value=round(total_predicted_score, 1), ground=100),
                tasteStructure=TasteStructure(
                    body=self._check_taste_body(total_body, language),
                    acidity=self._check_taste_acidity(total_acidity, language),
                    tannin=self._check_taste_tannin(total_tannin, language),
                    sweetness=self._check_taste_sweetness(total_sweetness, language),
                ),
                actualVotes=[Vote(
                    id=key,
                    name=REVIEW_QUALITY.to_name(key),
                    count=value
                ) for key, value in total_actual_vote.items()],
                predictedVotes=[Vote(
                    id=key,
                    name=REVIEW_QUALITY.to_name(key),
                    count=value
                ) for key, value in total_predicted_vote.items()],
                colors=total_colors[:5],
                aromas=total_aromas[:5],
                palates=total_palates[:5],
                pairings=total_pairings[:5],
                ingredients=total_ingredients[:5],
            )
        )
        
    ##############################################################
    # HELPER METHODS
    ##############################################################
    @staticmethod
    def _make_lookup_query(
        local_field: str,
        required_fields: List[str],
        collection: COLLECTION,
        as_field: Optional[str],
        foreign_field: Optional[str] = "_id"
    ) -> Dict[str, Any]:
        return {
            "from": collection.value,
            "localField": local_field,
            "foreignField": foreign_field,
            "as": as_field,
            "pipeline": [
                {
                    "$project": {
                        "_id": 0,
                        **{
                            field: 1 for field in required_fields
                        }
                    }
                }
            ]
        }
        
    
    
    @staticmethod
    def check_if_id_is_slug(_id: str) -> bool:
        parsed_ids = _id.split("-")
        id_suffix = parsed_ids[-1]
        if id_suffix.isdigit() or id_suffix == "nv":
            return False
        else:
            return True
        
    @staticmethod
    def _make_detail_canonical(slug: str, vintage: str, is_default: bool) -> str:
        if not is_default:
            return f"/wine/{slug}?vintage={vintage}"
        
        return f"/wine/{slug}"
    
    @staticmethod
    def _make_detail_meta(document: Dict[str, Any], language: str = "en") -> Meta:
        meta = document.get("meta") or {}
        
        title = meta["title"] if meta.get("title") else f"{document['name']} - Wine & News"
        description = meta["description"] if meta.get("description") else document["description"]
        
        if not description:
            description = (
                f"와인 & 뉴스에서 {document['name']} 와인에 대해 알아보세요. 이 와인에 대한 가격, 평점 및 리뷰를 확인하세요." if language == "ko"
                else f"ワインとニュースで {document['name']} を探索してください。価格、評価、レビューなど、このワインについて詳しく見てみましょう。" if language == "ja"
                else f"Explore {document['name']} with Wine & News. Find out more about this wine, including its price, ratings, and reviews."
            )
        
        keywords = meta["keywords"] if meta.get("keywords") else document["keywords"]
        if document["country"] and document["country"][0].get("name"):
            keywords.append(f'{document["country"][0]["name"]} Wines')
        if document["region"] and document["region"][0].get("name"):
            keywords.append(f'{document["region"][0]["name"]} Wines')
        
        keywords += [grape["name"] for grape in document["grape"]["items"]]
        keywords += [aroma["name"] for aroma in document["aroma"]["primary"]]
        keywords += [aroma["name"] for aroma in document["aroma"]["secondary"]]
        keywords += [aroma["name"] for aroma in document["aroma"]["tertiary"]]
        # keywords += [pairing["name"] for pairing in document["pairing"]["items"]]
        keywords = list(set(keywords))
        
        return Meta(
            title=title,
            description=description,
            keywords=keywords[:7]
        )
  
    def _check_taste_body(self, body: Optional[float], language: str) -> Optional[TasteChart]:
        if not body:
            return None
        
        body = int(body)
        if body >= 4:
            return TasteChart(
                name="무거운 바디감" if language == "ko" else "フルボディ" if language == "ja" else "Full Bodied",
                description=(
                    "풀 바디 와인은 풍부하고 복합적이며 강렬한 풍미와 긴 여운을 갖고 있습니다. 알코올과 탄닌 함량이 더 높은 경우가 많습니다. 스테이크나 양고기 같은 풍성한 요리와 잘 어울립니다." if language == "ko" else
                    "フルボディのワインは豊かで複雑で、強烈な風味と長い余韻を持っています。多くの場合、アルコールとタンニンが多く含まれています。ステーキやラム肉などのボリュームのある料理とよく合います。" if language == "ja" else
                    "Full-bodied wines are rich and complex, with intense flavors and a long finish. They are often higher in alcohol and tannins. They pair well with hearty dishes like steak or lamb."
                ),
                score=body,
            )
        elif body >= 2.5:
            return TasteChart(
                name="중간 바디감" if language == "ko" else "ミディアムボディ" if language == "ja" else "Medium Bodied",
                description=(
                    "미디엄 바디 와인은 다재다능하고 쉽게 마실 수 있으며 과일, 산도 및 탄닌의 균형이 좋습니다. 닭고기부터 파스타까지 다양한 음식과 잘 어울립니다." if language == "ko" else
                    "ミディアムボディのワインは多目的で飲みやすく、果実味、酸味、タンニンのバランスが取れています。鶏肉からパスタまで幅広い料理とよく合います。" if language == "ja" else
                    "Medium-bodied wines are versatile and easy to drink, with a good balance of fruit, acidity, and tannins. They pair well with a wide range of foods, from poultry to pasta."
                ),
                score=body,
            )
        else:
            return TasteChart(
                name="가벼운 바디감" if language == "ko" else "ライトボディ" if language == "ja" else "Light Bodied",
                description=(
                    "라이트 바디 와인은 가벼우며 상쾌하며 밝은 과일 풍미와 깔끔한 마무리가 특징입니다. 샐러드나 해산물과 같은 가벼운 요리와 잘 어울립니다." if language == "ko" else
                    "ライトボディのワインは軽やかで爽やかで、明るい果実味とさっぱりとしたフィニッシュが特徴です。サラダやシーフードなどの軽い料理とよく合います。" if language == "ja" else
                    "Light-bodied wines are delicate and refreshing, with bright fruit flavors and a crisp finish. They pair well with light dishes like salads or seafood."
                ),
                score=body,
            )
    
    def _check_taste_acidity(self, acidity: Optional[float], language: str) -> Optional[TasteChart]:
        if not acidity:
            return None
        
        acidity = int(acidity)
        if acidity >= 4:
            return TasteChart(
                name="높은 산미" if language == "ko" else "ハイアシディティ" if language == "ja" else "High Acidity",
                description=(
                    "높은 산미의 와인은 상쾌하고 깔끔하며 입안을 씻어주는 특징이 있습니다. 치즈나 튀긴 치킨과 같은 기름진 음식과 잘 어울립니다." if language == "ko" else
                    "ハイアシディティのワインはさわやかで明るく、口中をさっぱりとさせる特徴があります。チーズやフライドチキンなどの脂っこい食べ物とよく合います。" if language == "ja" else
                    "High acidity wines are crisp and refreshing, with a zesty, mouthwatering quality. They pair well with rich, fatty foods like cheese or fried chicken."
                ),
                score=acidity,
            )
        elif acidity >= 2.5:
            return TasteChart(
                name="중간 산미" if language == "ko" else "ミディアムアシディティ" if language == "ja" else "Medium Acidity",
                description=(
                    "중간 산미의 와인은 균형이 잡히고 다재다능하며 생기 넘치고 밝은 성격을 가지고 있습니다. 해산물부터 샐러드까지 다양한 음식과 잘 어울립니다." if language == "ko" else
                    "ミディアムアシディティのワインはバランスが取れており、多目的で生き生きとした明るい性格を持っています。シーフードからサラダまで幅広い料理とよく合います。" if language == "ja" else
                    "Medium acidity wines are balanced and versatile, with a lively, bright character. They pair well with a wide range of foods, from seafood to salads."
                ),
                score=acidity,
            )
        else:
            return TasteChart(
                name="낮은 산미" if language == "ko" else "ローアシディティ" if language == "ja" else "Low Acidity",
                description=(
                    "낮은 산미의 와인은 부드럽고 쉽게 마실 수 있으며 부드럽고 둥근 성격을 가지고 있습니다. 파스타나 리조또와 같은 풍부하고 크리미한 요리와 잘 어울립니다." if language == "ko" else
                    "ローアシディティのワインは滑らかで飲みやすく、柔らかく丸みのある性格を持っています。パスタやリゾットなどのリッチでクリーミーな料理とよく合います。" if language == "ja" else
                    "Low acidity wines are smooth and easy to drink, with a soft, rounded character. They pair well with rich, creamy dishes like pasta or risotto."
                ),
                score=acidity,
            )
            
    def _check_taste_tannin(self, tannin: Optional[float], language: str) -> Optional[TasteChart]:
        if not tannin:
            return None
        
        tannin = int(tannin)
        if tannin >= 4:
            return TasteChart(
                name="탄닌이 강한" if language == "ko" else "ハイタンニン" if language == "ja" else "High Tannin",
                description=(
                    "탄닌이 강한 와인은 대담하고 구조적이며 단단한 질감을 가지고 있습니다. 스테이크나 바베큐와 같은 기름진 음식과 잘 어울립니다." if language == "ko" else
                    "ハイタンニンのワインは大胆で構造的で、しっかりとした質感があります。ステーキやバーベキューなどの脂っこい食べ物とよく合います。" if language == "ja" else
                    "High tannin wines are bold and structured, with a firm, grippy texture. They pair well with rich, fatty foods like steak or barbecue"
                ),
                score=tannin,
            )
        elif tannin >= 2.5:
            return TasteChart(
                name="중간 탄닌" if language == "ko" else "ミディアムタンニン" if language == "ja" else "Medium Tannin",
                description=(
                    "중간 탄닌의 와인은 부드럽고 유연하며 균형잡힌 벨벳 같은 질감을 가지고 있습니다. 닭고기부터 파스타까지 다양한 음식과 잘 어울립니다." if language == "ko" else
                    "ミディアムタンニンのワインは滑らかでしなやかで、バランスの取れたベルベットのような質感を持っています。鶏肉からパスタまで幅広い料理とよく合います。" if language == "ja" else
                    "Medium tannin wines are smooth and supple, with a balanced, velvety texture. They pair well with a wide range of foods, from poultry to pasta."
                ),
                score=tannin,
            )
        else:
            return TasteChart(
                name="낮은 탄닌" if language == "ko" else "ロータンニン" if language == "ja" else "Low Tannin",
                description=(
                    "탄닌이 낮은 와인은 부드럽고 쉽게 마실 수 있으며 부드럽고 실키한 질감을 가지고 있습니다. 연어나 샐러드와 같은 가벼운 요리와 잘 어울립니다." if language == "ko" else
                    "ロータンニンのワインは滑らかで飲みやすく、柔らかくシルキーな質感を持っています。サーモンやサラダなどの軽い料理とよく合います。" if language == "ja" else
                    "Low tannin wines are soft and easy to drink, with a smooth, silky texture. They pair well with light dishes like salmon or salad."
                ),
                score=tannin,
            )
    
    def _check_taste_sweetness(self, sweetness: Optional[float], language: str) -> Optional[TasteChart]:
        if not sweetness:
            return None
        
        sweetness = int(sweetness)
        if sweetness >= 4:
            return TasteChart(
                name="스위트" if language == "ko" else "スウィート" if language == "ja" else "Sweet",
                description=(
                    "스위트 와인은 풍부하고 부드럽며 진한 과일 풍미와 부드러운 벨벳 같은 질감을 가지고 있습니다. 부드럽고 진한 디저트와 잘 어울립니다." if language == "ko" else
                    "スウィートワインは豊かで滑らかで、濃厚な果実味と滑らかなベルベットのような質感を持っています。リッチで濃厚なデザートとよく合います。" if language == "ja" else
                    "Sweet wines are rich and luscious, with intense fruit flavors and a smooth, velvety texture. They pair well with rich, decadent desserts."
                ),
                score=sweetness,
            )
        elif sweetness >= 3:
            return TasteChart(
                name="세미 스위트" if language == "ko" else "セミスウィート" if language == "ja" else "Semi-Sweet",
                description=(
                    "세미 스위트 와인은 과일향이 풍부하고 균형이 잡히며 약간의 달콤함과 상쾌한 마무리가 특징입니다. 카레나 바베큐와 같은 매운 요리와 잘 어울립니다." if language == "ko" else
                    "セミスウィートワインは果実味が豊かでバランスが取れ、少しの甘さとさっぱりとしたフィニッシュが特徴です。カレーやバーベキューなどの辛い料理とよく合います。" if language == "ja" else
                    "Semisweet wines are fruity and balanced, with a touch of sweetness and a crisp, refreshing finish. They pair well with spicy dishes like curry or barbecue."
                ),
                score=sweetness,
            )
        elif sweetness >= 2:
            return TasteChart(
                name="오프 드라이" if language == "ko" else "オフドライ" if language == "ja" else "Off-Dry",
                description=(
                    "오프 드라이 와인은 약간 달콤하고 과일향이 풍부하며 깔끔하고 상쾌한 마무리가 특징입니다. 태국 카레나 스시와 같은 매운 요리와 잘 어울립니다." if language == "ko" else
                    "オフドライワインは少し甘くて果実味が豊かで、さっぱりとした爽やかなフィニッシュが特徴です。タイカレーや寿司などの辛い料理とよく合います。" if language == "ja" else
                    "Off-dry wines are slightly sweet and fruity, with a hint of sweetness and a clean, refreshing finish. They pair well with spicy dishes like Thai curry or sushi."
                ),
                score=sweetness,
            )
        else:
            return TasteChart(
                name="드라이" if language == "ko" else "ドライ" if language == "ja" else "Dry",
                description=(
                    "드라이 와인은 상쾌하고 깔끔하며 감미료가 없으며 깔끔하고 상쾌한 마무리가 특징입니다. 해산물부터 샐러드까지 다양한 음식과 잘 어울립니다." if language == "ko" else
                    "ドライワインはさわやかで明るく、甘味がなくさっぱりとした爽やかなフィニッシュが特徴です。シーフードからサラダまで幅広い料理とよく合います。" if language == "ja" else
                    "Dry wines are crisp and refreshing, with no perceptible sweetness and a clean, zesty finish. They pair well with a wide range of foods, from seafood to salads."    
                ),
                score=sweetness,
            )
    
    def _check_quality(self, id: str) -> Optional[Element]:
        return Element(
            id=id,
            name=REVIEW_QUALITY.to_name(id)
        )
    
    def _make_100_point_score(self, value: float, ground: int) -> Optional[float]:
        if not value or not ground:
            return None
        
        return round(value / ground * 100, 2)
    
    def _make_highlight_text(self, source: Optional[float], target: Optional[float]) -> Optional[str]:
        gap_ratio = (target - source) / source if source and target else None
        
        if gap_ratio is None:
            return None

        return "" # TODO: highlight text 만들기

    def _calculate_price_for_value(self, source: Optional[Price], target: Optional[Price]) -> Optional[float]:
        if not source or not target:
            return None
        
        return round((target.value - source.value) / source.value * 100, 2)
    
    def _calculate_cost_effectiveness(self, price_for_value) -> Optional[int]:
        if not price_for_value:
            return None
        
        return (
            1 if price_for_value < -0.1
            else 0 if price_for_value < 0.1
            else -1
        )
        
    def _replace_to_multi_language(self, item: dict, language: str) -> dict:
        
        if language in ["ko", "ja"] and item.get(language):
            item["name"] = item[language].get("name") or item["name"]
            item["description"] = item[language].get("description", "")
            item["grape"]["description"] = item[language].get("grape", {}).get("description", "") if item[language].get("grape") else ""
            item["pairing"] = item[language].get("pairing", {})
            item["taste"]["description"] = item[language].get("taste", {}).get("description", "") if item[language].get("taste") else ""
            item["meta"] = item[language].get("meta", {})
            item["keywords"] = item[language].get("keywords", [])
            item["aroma"]["description"] = item[language].get("aroma", {}).get("description", "") if item[language].get("aroma") else ""
            item["highlights"] = item[language].get("highlights", [])
            
            item["types"] = [
                {
                    **type,
                    "name": type[language]["name"],
                } for type in item.get("types", [])
            ]
            item["country"] = [
                {
                    **country,
                    "name": country.get(language, {}).get("name") or country["name"],
                } for country in item.get("country", [])
            ]
            item["region"] = [
                {
                    **region,
                    "name": region.get(language, {}).get("name") or region["name"],
                    "summary": region.get(language, {}).get("summary")
                } for region in item.get("region", [])
            ]
            item["aroma"]["primary"] = [
                {
                    **aroma,
                    "name": aroma[language]["name"],
                } for aroma in item.get("aroma", {}).get("primary", []) if aroma.get(language, {}).get("name")
            ]
            item["aroma"]["secondary"] = [
                {
                    **aroma,
                    "name": aroma[language]["name"],
                } for aroma in item.get("aroma", {}).get("secondary", []) if aroma.get(language, {}).get("name")
            ]
            item["aroma"]["tertiary"] = [
                {
                    **aroma,
                    "name": aroma[language]["name"],
                } for aroma in item.get("aroma", {}).get("tertiary", []) if aroma.get(language, {}).get("name")
            ]
            
        return item
    