from collections import Counter, defaultdict
from functools import cached_property

import httpx
import spacy
import streamlit as st

nlp = spacy.load("fr_core_news_lg", exclude=["ner"])


class Scrapper:

    def __init__(self, db=None):
        self.db = db

    @cached_property
    def bearer_token(self):
        url = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
        user_id = "PAR_copeelotelab_ea09b1e3cd6e09b6c329507978ed8c5bf1d8ef8f820a5d350d3be0afbcdce610"
        user_secret = "0ecf9ceb410cba1a4ca6b075b53ff980bdcbee8b4c3ca35e9603e96cdb0847ee"
        payload = {
            "grant_type": "client_credentials",
            "client_id": user_id,
            "client_secret": user_secret,
            "scope": "api_offresdemploiv2 o2dsoffre"
        }
        res = httpx.post(url, params={"realm": "/partenaire"}, data=payload)
        res.raise_for_status()
        return res.json().get("access_token")

    def query(self, params=None, endpoint="/offres/search"):
        url = f"https://api.francetravail.io/partenaire/offresdemploi/v2{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}"
        }
        res = httpx.get(url, params=params, headers=headers)
        res.raise_for_status()
        return res

    def iterate(self, params, limit):
        start = 0
        total = None
        while total is None or (start < total and start < min(limit, 3000)):
            try:
                params["range"] = f"{start}-{start + 100}"
                res = self.query(params)
            except httpx.HTTPStatusError as e:
                st.write(e)
                break
            content_range = res.headers.get("Content-Range")
            parts = content_range.split("/")
            data = res.json()
            total = int(parts[-1])
            for result in data.get("resultats", []):
                # self.progress.progress(min(start / min(total, self.limit), 1.0))
                start += 1
                yield self.find_keywords(result)
            start = int(parts[0].split("-")[-1])

    @staticmethod
    def find_keywords(document):
        document["counters"] = defaultdict(Counter)
        for weight, text in [(1, document.get("description")), (3, document.get("intitule"))]:
            doc = nlp(text)
            for w in doc:
                if not w.is_stop and w.is_alpha:
                    # st.write(str((w.pos_, w.lemma_)))
                    document["counters"][w.pos_][w.lemma_] += weight
        return document

    @staticmethod
    def score_matching(doc1, doc2, vocab):
        doc1_counter_all = Counter()
        doc2_counter_all = Counter()
        for pos, counter in doc1.get("counters", {}).items():
            doc1_counter_all.update(counter)
        for pos, counter in doc2.get("counters", {}).items():
            doc2_counter_all.update(counter)
        intersection = doc1_counter_all & doc2_counter_all
        addition = doc1_counter_all + doc2_counter_all
        for word in intersection:
            if word not in vocab:
                intersection.pop(word)
            else:
                intersection[word] = addition[word]
        return sum(intersection.values())

    def run(self, parameters, limit):
        self.db.insert(self.iterate(parameters, limit), get_id=lambda x: x["id"])
