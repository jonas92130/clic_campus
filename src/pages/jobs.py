import streamlit as st

from pages.utils import Scrapper, Db

st.header("Create job collection")

# col1, col2 = st.columns(2)

scrapper = Scrapper()


@st.cache_data
def departement():
    return scrapper.query(endpoint="/referentiel/departements").json()


@st.cache_data
def domaines():
    return scrapper.query(endpoint="/referentiel/domaines").json()


with st.sidebar:
    with st.form("run", border=False):
        deps = departement()
        departement = st.selectbox("Département", [None] + [d["code"] for d in deps],
                                   format_func=lambda x: "Tous" if not x else
                                   [d["libelle"] for d in deps if d["code"] == x][0])
        doms = domaines()
        domaine = st.selectbox("Domaine", [None] + [d["code"] for d in doms],
                                        format_func=lambda x: "Tous" if not x else
                                        [d["libelle"] for d in doms if d["code"] == x][0])
        limit = st.slider("Limit", 1, 10000, 10)
        collection = st.text_input("Collection")
        st.write("Or select an existing collection")
        selected_collection = st.selectbox("Collection", Db.get_collections("jobs"))
        job_collection = collection or selected_collection
        if st.form_submit_button("Run"):
            st.session_state["job_collection"] = job_collection
            scrapper.db = Db.get_db("jobs", job_collection)
            scrapper.run(parameters={"departement": departement, "domaine": domaine}, limit=limit)

if job_collection := st.session_state.get("job_collection"):
    for i, doc in enumerate(Db.get_documents("jobs", [job_collection])):
        st.write(doc)
        if i > 10:
            break
