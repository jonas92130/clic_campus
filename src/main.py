import json
from collections import Counter, defaultdict
from functools import cached_property

import httpx
import spacy
import streamlit as st

nlp = spacy.load("fr_core_news_lg", exclude=["ner"])


class Scrapper:

    def __init__(self, limit=3000):
        self.counters = defaultdict(Counter)
        self.limit = limit
        # self.progress = st.progress(0)

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

    def iterate(self, params):
        start = 0
        total = None
        while total is None or (start < total and start < self.limit):
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
                yield result
            start = int(parts[0].split("-")[-1])

    def find_keywords(self, document):
        for weight, text in [(1, document.get("description")), (3, document.get("intitule"))]:
            doc = nlp(text)
            for w in doc:
                if not w.is_stop and w.is_alpha:
                    # st.write(str((w.pos_, w.lemma_)))
                    self.counters[w.pos_][w.lemma_] += weight

    def save(self, path="offers.json"):
        docs = []
        for offer in self.iterate({}):
            docs.append(offer)
            self.find_keywords(offer)
        json.dump(docs, open(path, "w"))

    def run(self, key, values, limit):
        self.limit = limit
        for value in values:
            for offer in self.iterate({key: value}):
                self.find_keywords(offer)
        return self.counters


scrapper = Scrapper()


@st.cache_data
def run(key, values, limit):
    return scrapper.run(key, values, limit)


@st.cache_data
def departement():
    return scrapper.query(endpoint="/referentiel/departements").json()

if __name__ == "__main__":
    # st.write(scrapper.run("ville", ["Paris", "Lyon", "Marseille"]))
    with st.sidebar:
        uploaded_files = st.file_uploader("Upload", type=["json", "txt"], accept_multiple_files=True)
        if not st.session_state.get("vocabulary"):
            st.session_state["vocabulary"] = set()
        if uploaded_files:
            for uploaded_file in uploaded_files:
                if uploaded_file.type == "txt":
                    for line in uploaded_file:
                        st.session_state["vocabulary"].add(line.strip())
                else:
                    data = json.load(uploaded_file)
                    for word in data:
                        st.session_state["vocabulary"].add(word)

        deps = departement()
        key = st.selectbox("Key", ["departement"])
        values = st.multiselect("Values", [d["code"] for d in deps],
                                format_func=lambda x: [d["libelle"] for d in deps if d["code"] == x][0])
        limits = st.slider("Limit", 1, 10000, 10)
        counters = run(key, values, limit=limits)
        for name, counter in counters.items():
            for word in st.session_state["vocabulary"]:
                counter.pop(word, None)
        option = st.selectbox(
            'POS',
            ["all"] + list(counters))
        nb_values = st.slider("Top", 1, 1000, 100)
        counters["all"] = sum(counters.values(), Counter())
    col1, col2 = st.columns(2)
    with col1:
        with st.form('vocab_form'):
            select_all = st.checkbox("Select All", value=True)

            checkboxes = []
            # st.header("Vocabulary")
            data = list(st.session_state["vocabulary"])
            data.sort()
            with st.container(height=500):
                for word in data:
                    checkboxes.append((st.checkbox(f"{word}", value=select_all), word))
            # st.write(data)
            st.download_button("Download", json.dumps(list(st.session_state["vocabulary"])),
                               "words.json", "application/json")
    with col2:
        if option:
            # @st.experimental_fragment
            # def checkboxes():
            if not st.session_state.get("words"):
                st.session_state["words"] = set(counters["all"].most_common(nb_values))
            select_all = st.checkbox("Select All", value=True, key="words_select_all")
            with st.form('words_form'):
                checkboxes = []
                with st.container(height=500, border=False):
                    for word, count in counters[option].most_common(nb_values):
                        checkboxes.append((st.checkbox(f"{word} ({count})", value=select_all), word))
                if st.form_submit_button('Add to my vocabulary', type="primary"):
                    st.session_state["vocabulary"].update(set([word for checked, word in checkboxes if checked]))
                    st.experimental_rerun()

            # st.write(st.session_state["vocabulary"])
            # st.write([word for checked, word in checkboxes if checked])

# find_keywords(offer.get("description"), weight=1)
# find_keywords(offer.get("intitule"), weight=3)
# print(counter.most_common(100))
