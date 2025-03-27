from typing import Any, Dict, List, Tuple, Union

import certifi
from pymongo import MongoClient, ReadPreference
from pymongo.errors import PyMongoError


class MongoDB:
    def __init__(self, host: str, username: str, password: str, database: str):
        self._client = self._open_client(host, username, password)
        self._read_db = self._get_secondary_database(database)
        self._write_db = self._get_primary_database(database)

    def _open_client(self, host: str, username: str, password: str):
        return MongoClient(
            f"mongodb+srv://{username}:{password}@{host}",
            w="majority",
            compressors="zstd",
            maxPoolSize=100,
            tlsCAFile=certifi.where(),
            retryWrites=True,
            read_preference=ReadPreference.NEAREST
        )

    def _get_primary_database(self, database: str):
        return self._client[database]

    def _get_secondary_database(self, database: str):
        return self._client.get_database(
            name=database, 
            read_preference=ReadPreference.SECONDARY_PREFERRED
        )

    def _close_client(self):
        self._client.close()

    def get_document(
        self,
        collection: str,
        query: Dict[str, Union[str, int, Any]],
        projection: Dict[str, Union[str, int, Any]]
    ) -> Dict[str, Union[str, int, Any]]:
        doc = self._read_db.get_collection(collection).find_one(
            filter=query, 
            projection=projection
        )
        return dict(doc) if (doc is not None) else dict()

    def aggregate_documents(
        self,
        collection: str,
        pipelines: List[Dict[str, Union[str, int, Any]]]
    ) -> Dict[str, Union[str, int, Any]]:
        docs = self._read_db.get_collection(collection).aggregate(pipelines)
        return list(docs) if (docs is not None) else list()

    def get_documents(
        self,
        collection: str,
        query: Dict[str, Union[str, int, Any]],
        projection: Dict[str, Union[str, int, Any]],
        sort: List[Tuple[str, int]] = None,
        limit: int = None
    ) -> Dict[str, Union[str, int, Any]]:
        if sort and limit:
            docs = (
                self._read_db.get_collection(collection)
                .find(query, projection)
                .sort(sort)
                .limit(limit)
            )
        elif sort:
            docs = (
                self._read_db.get_collection(collection)
                .find(query, projection)
                .sort(sort)
            )
        elif limit:
            docs = (
                self._read_db.get_collection(collection)
                .find(query, projection)
                .limit(limit)
            )
        else:
            docs = self._read_db.get_collection(collection).find(
                query, projection
            )
        return list(docs) if (docs is not None) else list()

    def upsert_document(
        self,
        collection: str,
        query: Dict[str, Union[str, int, Any]],
        update_query: Dict[str, Union[str, int, Any]]
    ):
        doc = self._write_db[collection].update_one(query, update_query, upsert=True)
        if not doc.acknowledged:
            raise PyMongoError("DB Upsert Error")
        return doc.upserted_id

    def update_document(
        self,
        collection: str,
        query: Dict[str, Union[str, int, Any]],
        update_query: Dict[str, Union[str, int, Any]]
    ):
        doc = self._write_db[collection].update_one(query, update_query, upsert=False)
        if not doc.acknowledged:
            raise PyMongoError("DB Update Error")
        return doc

    def update_documents(
        self,
        collection: str,
        query: Dict[str, Union[str, int, Any]],
        update_query: Dict[str, Union[str, int, Any]]
    ):
        doc = self._write_db[collection].update_many(query, update_query, upsert=False)
        if not doc.acknowledged:
            raise PyMongoError("DB Update Error")
        return doc

    def create_document(
        self,
        collection: str,
        document: Dict[str, Union[str, int, Any]]
    ):
        doc = self._write_db[collection].insert_one(document=document)
        if not doc.acknowledged:
            raise PyMongoError("DB Insert Error")
        return doc.inserted_id

    def bulk_update_documents(
        self,
        collection: str,
        bulk_operations: list
    ):
        doc = self._write_db[collection].bulk_write(bulk_operations)
        if not doc.acknowledged:
            raise PyMongoError("DB Update Error")
        return doc

    @staticmethod
    def make_lookup_query(
        as_field: str,
        collection: str,
        local_field: str,
        required_fields: List[str],
        foreign_field: str = "_id",
    ) -> Dict[str, Any]:
        return {
            "from": collection,
            "localField": local_field,
            "foreignField": foreign_field,
            "as": as_field,
            "pipeline": [
                {
                    "$project": {
                        "_id": 0,
                        **{
                            field: 1 
                            for field in required_fields
                        }
                    }
                }
            ]
        }
        
    @staticmethod
    def make_pagination_facet_query(page: int, size: int) -> Dict[str, Any]:
        return {
            "items": [
                {"$skip": (page - 1) * size},
                {"$limit": size}
            ],
            "total": [
                {"$count": "count"}
            ]
        }