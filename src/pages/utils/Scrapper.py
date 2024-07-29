from collections import Counter, defaultdict
from functools import cached_property, cache

import httpx
import spacy
import streamlit as st
from wordfreq import zipf_frequency

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
    def _check_word(w, vocab=None):
        return not w.is_stop and w.is_alpha and (vocab is None or w.lemma_ not in vocab)


    @staticmethod
    def find_keywords(document, vocab=None):
        document["counters"] = defaultdict(Counter)
        for weight, text in [(1, document.get("description")), (3, document.get("intitule"))]:
            doc = nlp(text)
            for sentence in doc.sents:
                for i1, w1 in enumerate(sentence):
                    if Scrapper._check_word(w1, vocab):
                        document["counters"][w1.pos_][w1.lemma_] += weight
                        for i2, w2 in enumerate(sentence[i1 + 1:]):
                            if Scrapper._check_word(w2, vocab):
                                document["counters"]["bi_gram"][f"{w1.lemma_} {w2.lemma_}"] += weight * 2
                                for w3 in sentence[i1 + i2 + 2:]:
                                    if Scrapper._check_word(w3, vocab):
                                        document["counters"]["tri_gram"][f"{w1.lemma_} {w2.lemma_} {w3.lemma_}"] += weight * 3
                                        break
                                break
        return document

    @staticmethod
    @cache
    def most_similar(word, topn=15):
        st.write(f"{word} ({zipf_frequency(word, 'fr')})")
        if " " in word:
            return []
        word = nlp.vocab[str(word)]
        queries = [
            nlp.vocab[w] for w in nlp.vocab.vectors
            if nlp.vocab[w].is_lower == word.is_lower
        ]

        by_similarity = sorted(queries, key=lambda w: word.similarity(w), reverse=True)
        res = [(str(w.lower_), float(w.similarity(word)), zipf_frequency(w.lower_, 'fr')) for w in by_similarity[:topn + 1] if w.lower_ != word.lower_]
        st.write(res)
        return res

    @staticmethod
    def score_matching(doc1, doc2, vocab):
        doc1_counter_all = Counter()
        doc2_counter_all = Counter()
        for pos, counter in doc1.get("counters", {}).items():
            doc1_counter_all.update(counter)
        for pos, counter in doc2.get("counters", {}).items():
            doc2_counter_all.update(counter)
            for elem in counter:
                freq = zipf_frequency(elem, "fr")
                coef = (1 + 8 / freq if freq > 0 else 0) ** 3
                doc2_counter_all[elem] = doc2_counter_all[elem] * coef
                for word, similarity, freq in Scrapper.most_similar(elem):
                    if word not in doc2_counter_all:
                        freq = zipf_frequency(word, "fr")
                        coef = (1 + 1 / freq if freq > 0 else 0) ** 3
                        doc2_counter_all[word] = similarity * (coef ** 2)
        intersection = doc1_counter_all & doc2_counter_all
        addition = doc1_counter_all + doc2_counter_all
        for word in intersection:
            if word in vocab:
                intersection[word] = 0
            else:
                intersection[word] = addition[word]
        doc1["matched_keywords"] = intersection
        doc1["experience_keywords"] = doc2_counter_all
        return sum(intersection.values())

    def run(self, parameters, limit):
        self.db.insert(self.iterate(parameters, limit), get_id=lambda x: x["id"])
