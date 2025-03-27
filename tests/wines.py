import logging
from http import HTTPStatus

from chalice.test import Client

from app import app
from chalicelib.src.constants.common import COLLECTION, STATUS
from chalicelib.src.tools.database import mongodb_obj

logger = logging.getLogger("wines")

API_PREFIX = "/api/v1.3"
API_HEADER = {
    "Accept": "application/json",
    "Accept-Language": "en"
}

class TestWine:
    collection = COLLECTION.WINE.value
    
    def run(self):
        self.test_get_detail()
    
    def test_get_detail(self):
        """
            GET /v1.3/wines/{id}
        """
        items = self._fetch_wines_from_db()
        logger.info(f"Total items: {len(items)}")
        
        with Client(app) as client:            
            for item in items:
                for language in ["ko", "en", "ja"]:
                    API_HEADER["Accept-Language"] = language
                    endpoint = f"{API_PREFIX}/wines/{item['_id']}"
                    response = client.http.get(endpoint, headers=API_HEADER)
                    if self._check_if_response_is_ok(response.status_code):
                        # logger.info(f"\n GET {endpoint}: {response.status_code}")
                        pass
                    else:
                        logger.error(f"\n GET {endpoint}: {response.status_code} {response.json_body}")
            
    def _fetch_wines_from_db(self):
        query = {
            # "status": {
            #     "$gte": STATUS.PUBLISHED.value
            # }
        }
        project_query = {"_id": 1}
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
    test = TestWine()
    test.test_get_detail()