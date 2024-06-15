import streamlit as st

from pages.utils import Scrapper, Db

st.header("Create job collection")

# col1, col2 = st.columns(2)

scrapper = Scrapper()


@st.cache_data
def departement():
    return scrapper.query(endpoint="/referentiel/departements").json()


@st.cache_data
def secteur_activite():
    return scrapper.query(endpoint="/referentiel/secteursActivites").json()


with st.sidebar:
    with st.form("run", border=False):
        deps = departement()
        departement = st.selectbox("Département", [d["code"] for d in deps],
                                   format_func=lambda x: [d["libelle"] for d in deps if d["code"] == x][0])
        sects = secteur_activite()
        secteur_activite = st.selectbox("Secteur d'activité", [d["code"] for d in sects],
                                        format_func=lambda x: [d["libelle"] for d in sects if d["code"] == x][0])
        limit = st.slider("Limit", 1, 10000, 10)
        collection = st.text_input("Collection")
        st.write("Or select an existing collection")
        selected_collection = st.selectbox("Collection", Db.get_collections("jobs"))
        job_collection = collection or selected_collection
        if st.form_submit_button("Run"):
            st.session_state["job_collection"] = job_collection
            scrapper.db = Db.get_db("jobs", job_collection)
            scrapper.run(parameters={"departement": departement, "secteurActivite": secteur_activite}, limit=limit)

if job_collection := st.session_state.get("job_collection"):
    for doc in Db.get_documents("jobs", [job_collection]):
        st.write(doc)
