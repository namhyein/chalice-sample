import logging
from http import HTTPStatus

from chalice.test import Client

from app import app

logger = logging.getLogger("modules")

API_PREFIX = "/api/v1.3"
API_HEADER = {
    "Accept": "application/json",
    "Accept-Language": "en"
}

class TestModule:
    
    def run(self):
        self.test_home()
    
    def test_home(self):
        """
            GET /v1.3/home
        """
        
        with Client(app) as client:            
            for language in ["ko", "en", "ja"]:
                API_HEADER["Accept-Language"] = language
                endpoint = f"{API_PREFIX}/home"
                response = client.http.get(endpoint, headers=API_HEADER)
                if self._check_if_response_is_ok(response.status_code):
                    logger.info(f"\n GET {endpoint}: {response.status_code}")
                else:
                    logger.error(f"\n GET {endpoint}: {response.status_code} {response.json_body}")
        
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
    test = TestModule()
    test.test_home()