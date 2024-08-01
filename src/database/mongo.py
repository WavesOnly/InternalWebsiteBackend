from pymongo import MongoClient
from dotenv import load_dotenv
from os import environ
from typing import Union, Optional, List, Tuple
import certifi


class Mongo:
    def __init__(self):
        load_dotenv(".env")
        self.client = MongoClient(environ["MONGO_CONNECTION_STRING"], tlsCAFile=certifi.where())
        self.db = self.client["InternalWebsite"]

    def insert(self, collection: str, document: dict) -> str:
        id = self.db[collection].insert_one(document=document)
        return id

    def update(self, collection: str, id: dict, query: dict, upsert: bool) -> str:
        id = self.db[collection].update_one(id, query, upsert=upsert)
        return id

    def one(self, collection: str, query: dict) -> dict:
        document = self.db[collection].find_one(query)
        if document:
            {**document, "_id": str(document["_id"])}
        return document

    def all(
        self,
        collection: str,
        query: dict,
        sort: Optional[Union[List[Tuple[str, int]], Tuple[str, int]]] = None,
        serialize: bool = True,
    ) -> list:
        cursor = self.db[collection].find(query)
        if sort:
            cursor = cursor.sort(sort)
        return (
            [{**document, "_id": str(document["_id"])} for document in cursor]
            if serialize
            else [{**document} for document in cursor]
        )

    def pipeline(self, collection: str, query: list) -> List:
        cursor = list(self.db[collection].aggregate(query))
        return [{**document} for document in cursor]


mongo = Mongo()
