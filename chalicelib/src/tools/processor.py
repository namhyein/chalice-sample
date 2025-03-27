from typing import Any, Dict, List, Tuple

from chalicelib.src.constants.common import COLLECTION
from chalicelib.src.tools.database import mongodb_obj
from chalicelib.src.validators.field import Market, MarketPrice


class PriceProcessor:
    country_map = None
    currency_map = None
    
    def __init__(self):
        if not self.currency_map:
            # initialize currency map if not already initialized
            PriceProcessor.currency_map = self._initialize_currency_map()
        if not self.country_map:
            # initialize country map if not already initialized
            PriceProcessor.country_map = self._initialise_country_map()
    
    def _initialize_currency_map(self):
        currencies = self._fetch_currency_from_db()
        return {
            currency["code"]: currency for currency in currencies
        }
    
    def _initialise_country_map(self):
        countries = self._fetch_country_from_db()
        return {
            **{country["_id"]: country for country in countries},
            **{country["alpha_2"]: country for country in countries},
        }
    
    @staticmethod
    def _fetch_currency_from_db():
        query = {}
        projection = {
            "_id": 0, 
            "to": 1, 
            "from": 1, 
            "code": 1, 
            "symbol": 1
        }
        return mongodb_obj.get_documents(
            query=query,
            projection=projection,
            collection=COLLECTION.CURRENCY.value,
        )
    
    @staticmethod
    def _fetch_country_from_db():
        query = {}
        projection = {
            "_id": 1, 
            "name": 1,
            "alpha_2": 1,
            "alpha_3": 1,
            "currency_code": 1
        }
        return mongodb_obj.get_documents(
            query=query,
            projection=projection,
            collection=COLLECTION.COUNTRY.value,
        )
    
    def make_price_string(self, location: str, price: Dict[str, Any]) -> str:
        """
            price?: {
                united-states: [
                    {
                        value: FLOAT,
                        currency: STRING,
                        original_price: {
                            value: FLOAT,
                            currency: STRING,
                            bottle_count: INTEGER,
                            volume: INTEGER
                        },
                        market: {
                            name: STRING,
                            url: STRING,
                            is_auction: BOOLEAN,
                            product_name?: STRING,
                            shipping_info?: STRING,
                            tax_info?: STRING
                        }
                    }
                ]
            }
        """
        prices = self.select_local_prices(location=location, price=price)
        return self.to_string(prices=prices)
    
    def select_local_prices(self, location: str, price: Dict[str, Any]) -> List[MarketPrice]:
        """
            price?: {
                united-states: [
                    {
                        value: FLOAT,
                        currency: STRING,
                        original_price: {
                            value: FLOAT,
                            currency: STRING,
                            bottle_count: INTEGER,
                            volume: INTEGER
                        },
                        market: {
                            name: STRING,
                            url: STRING,
                            is_auction: BOOLEAN,
                            product_name?: STRING,
                            shipping_info?: STRING,
                            tax_info?: STRING
                        }
                    }
                ]
            }
        """
        if not price:
            return []

        # check currency
        country_id, currency = self._check_country_and_currency(location)
        return self.convert_to_market_prices(
            price={
                country_id: price[country_id]
            } if price.get(country_id) else price,
            currency=currency
        )
        
    def to_string(self, prices: List[MarketPrice]) -> str:
        if not prices:
            return ""
        
        symbol = prices[0].symbol
        value = self.get_minimum_price(prices=prices)
        value = "{:,}".format(int(value))
        return f"{symbol} {value}"

    def convert_to_market_prices(self, price: Dict[str, Any], currency: str) -> List[MarketPrice]:
        """
            price?: {
                united-states: [
                    {
                        value: FLOAT,
                        currency: STRING,
                        original_price: {
                            value: FLOAT,
                            currency: STRING,
                            bottle_count: INTEGER,
                            volume: INTEGER
                        },
                        market: {
                            name: STRING,
                            url: STRING,
                            is_auction: BOOLEAN,
                            product_name?: STRING,
                            shipping_info?: STRING,
                            tax_info?: STRING
                        }
                    }
                ]
            }
        """
        
        if not price:
            return []

        all_prices = []
        for country, prices in price.items():
            if country not in self.country_map:
                continue
            
            for price in prices:
                try:
                    all_price = self.convert_to_market_price(country=country, currency=currency, price=price)
                    all_prices.append(all_price)
                except:
                    continue
                    
        return all_prices

    def convert_to_market_price(self, 
                                country: str, 
                                currency: str, 
                                price: Dict[str, Any]) -> List[MarketPrice]:
        
        """
            price: {
                value: FLOAT,
                currency: STRING,
                original_price: {
                    value: FLOAT,
                    currency: STRING,
                    bottle_count: INTEGER,
                    volume: INTEGER
                },
                market: {
                    name: STRING,
                    url: STRING,
                    is_auction: BOOLEAN,
                    product_name?: STRING,
                    shipping_info?: STRING,
                    tax_info?: STRING
                }
            }
        """
        return MarketPrice(currency=currency,
                           symbol=self.currency_map[currency]["symbol"],
                           value=self._convert_price_value(currency=currency, price=price),
                           bottleCount=price["original_price"]["bottle_count"],
                           country=self.country_map[country]["alpha_2"],
                           market=Market(**price["market"]))
    
    
    def get_minimum_price(self, prices: List[MarketPrice]) -> float:
        """
            prices: [
                {
                    value: FLOAT,
                    currency: STRING,
                    bottle_count: INTEGER,
                    volume: INTEGER,
                    market: {
                        name: STRING,
                        url: STRING,
                        is_auction: BOOLEAN
                    }
                }
            ]
            
            - Get the minimum price from the list of prices
            - Format the price to have only 1 decimal place
        """    

        min_price = min(prices, key=lambda price: price.value)
        return round(min_price.value, 1)

    def get_average_price(self, prices: List[MarketPrice]) -> float:
        """
            prices: [
                {
                    value: FLOAT,
                    currency: STRING,
                    bottle_count: INTEGER,
                    volume: INTEGER,
                    market: {
                        name: STRING,
                        url: STRING,
                        is_auction: BOOLEAN
                    }
                }
            ]
            
            - Get the average price from the list of prices
            - Format the price to have only 1 decimal place
        """
        avg_value = sum([price.value for price in prices]) / len(prices)
        return round(avg_value, 1)

    def _convert_price_value(self, currency: str, price: Dict[str, Any]) -> float:
        """
            price: {
                value: FLOAT,
                currency: STRING,
            }
        """
        value = self._to_usd(price["currency"], price["value"])
        return self._to_currency(currency, value)

    def _to_usd(self, currency: str, price: float) -> float:
        return (
            price if currency == "USD" else
            price * self.currency_map[currency]["to"]
        )

    def _to_currency(self, currency: str, price: float) -> float:
        return (
            price if currency == "USD" else
            price * self.currency_map[currency]["from"]
        )
        
    def _check_country_and_currency(self, location: str) -> Tuple[str, str]:
        location = location or "US"
        location = location if location in self.country_map else "US"
        
        country_dict = self.country_map[location]
        return country_dict["_id"], country_dict["currency_code"]
        