from pymongo import MongoClient
from .Scrapper import Scrapper
from os import environ
try:
    with open("/home/jonas/Copeelote/clic_campus/src/.env") as f:
        for line in f:
            key, value = line.strip().split('="')
            environ[key] = value
except FileNotFoundError:
    print("No .env file found")

client = MongoClient(environ["MONGO_URI"])

mongo = client.clic_campus

from .Db import Db
