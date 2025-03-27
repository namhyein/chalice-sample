import logging
import random
from http import HTTPStatus

from chalice.test import Client

from app import app
from chalicelib.src.constants.article import ARTICLE_CATEGORY
from chalicelib.src.constants.common import COLLECTION, STATUS
from chalicelib.src.tools.database import mongodb_obj

logger = logging.getLogger("articles")

API_PREFIX = "/api/v1.3"
API_HEADER = {
    "Accept": "application/json",
    "Accept-Language": "en"
}

class TestArticle:
    collection = COLLECTION.ARTICLE.value
    
    def run(self):
        self.test_get_main()
        self.test_get_list()
        self.test_get_detail()
    
    def test_get_main(self):
        """
            GET /v1.3/article
        """
        with Client(app) as client:
            endpoint = f"{API_PREFIX}/article"
            response = client.http.get(endpoint, headers=API_HEADER)
            if self._check_if_response_is_ok(response.status_code):
                logger.info(f"\n GET {endpoint}: {response.status_code}")
            else:
                logger.error(f"\n GET {endpoint}: {response.status_code} {response.json_body}")
    
    def test_get_list(self):
        """
            GET /v1.3/articles
        """
        categories = ARTICLE_CATEGORY.__member_values__()
        logger.info(f"Total categories: {len(categories)}")
        
        with Client(app) as client:
            for category in categories:
                endpoint = f"{API_PREFIX}/articles?category={category}"
                
                response = client.http.get(endpoint, headers=API_HEADER)
                if self._check_if_response_is_ok(response.status_code):
                    logger.info(f"\n GET {endpoint}: {response.status_code}")
                else:
                    logger.error(f"\n GET {endpoint}: {response.status_code} {response.json_body}")

                page = random.randint(1, 3)
                size = random.randint(1, 10)
                endpoint = f"{API_PREFIX}/articles?category={category}&page={page}&size={size}"
                response = client.http.get(endpoint, headers=API_HEADER)
                if self._check_if_response_is_ok(response.status_code):
                    logger.info(f"\n GET {endpoint}: {response.status_code}")
                else:
                    logger.error(f"\n GET {endpoint}: {response.status_code} {response.json_body}")
    
    def test_get_detail(self):
        """
            GET /v1.3/articles/{id}
        """
        items = self._fetch_articles()
        logger.info(f"Total items: {len(items)}")
        
        with Client(app) as client:            
            for item in items:
                for language in ["ko", "en", "ja"]:
                    API_HEADER["Accept-Language"] = language
                    
                    endpoint = f"{API_PREFIX}/articles/{item['_id']}?category={item['category']['_id']}"
                    response = client.http.get(endpoint, headers=API_HEADER)
                    if self._check_if_response_is_ok(response.status_code):
                        logger.info(f"\n GET {endpoint}: {response.status_code}")
                    else:
                        logger.error(f"\n GET {endpoint}: {response.status_code} {response.json_body}")
                
                endpoint = f"{API_PREFIX}/articles/{item['_id']}/comments"
                response = client.http.get(endpoint, headers=API_HEADER)
                if self._check_if_response_is_ok(response.status_code):
                    logger.info(f"\n GET {endpoint}: {response.status_code}")
                else:
                    logger.error(f"\n GET {endpoint}: {response.status_code} {response.json_body}")
                        
    def _fetch_articles(self):
        query = {
            "status": {
                "$gte": STATUS.PUBLISHED.value
            }
        }
        project_query = {"_id": 1, "category._id": 1}
        return mongodb_obj.get_documents(
            query=query,
            projection=project_query,
            collection=self.collection,
        )
        
    @staticmethod
    def _check_if_response_is_ok(status: int):
        return status == HTTPStatus.OK
    
    @staticmethod
    def _check_if_response_is_redirected(status: int):
        return status == HTTPStatus.MOVED_PERMANENTLY
    
    @staticmethod
    def _check_if_response_is_not_found(status: int):
        return status == HTTPStatus.NOT_FOUND
    
    @staticmethod
    def _check_if_response_is_bad_request(status: int):
        return status == HTTPStatus.BAD_REQUEST
    

if __name__ == "__main__":
    test = TestArticle()
    test.test_get_main()
    test.test_get_list()
    test.test_get_detail()