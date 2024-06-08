from collections import Counter, defaultdict

from pymongo import UpdateOne

from pages.utils import mongo


class Db:

    def __init__(self, collection):
        self.collection = collection

    @classmethod
    def get_collections(cls, namespace):
        return [col[len(namespace) + 1:] for col in mongo.list_collection_names() if col.startswith(namespace)]

    @classmethod
    def get_db(cls, namespace, name):
        return cls(f"{namespace}_{name}")

    def insert(self, generator, get_id=None):
        batch = []
        for doc in generator:
            if get_id:
                doc["_id"] = get_id(doc)
            batch.append(UpdateOne({'_id': doc['_id']}, {'$setOnInsert': doc}, upsert=True))
            if len(batch) == 100:
                mongo[self.collection].bulk_write(batch, ordered=False)
                batch = []
        if batch:
            mongo[self.collection].bulk_write(batch, ordered=False)

    @classmethod
    def get_counters(cls, collections, remove_words=None):
        counters = defaultdict(Counter)
        for collection in collections:
            for doc in mongo[f"jobs_{collection}"].find():
                for pos, counter in doc.get("counters", {}).items():
                    counters[pos].update(counter)
                    counters["ALL"].update(counter)
        if remove_words:
            for word in remove_words:
                for counter in counters.values():
                    counter.pop(word, None)
        return counters

    @classmethod
    def get_ids(cls, namespace, collections):
        ids = set()
        for collection in collections:
            for doc in mongo[f"{namespace}_{collection}"].find():
                ids.add(doc["_id"])
        data = list(ids)
        data.sort()
        return data

    def remove_ids(self, ids):
        mongo[self.collection].delete_many({"_id": {"$in": ids}})
