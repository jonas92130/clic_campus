from pymongo import MongoClient
from .Scrapper import Scrapper
from os import environ

client = MongoClient(environ.get("MONGO_URI"))

mongo = client.clic_campus

from .Db import Db
