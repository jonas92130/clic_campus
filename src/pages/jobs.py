import streamlit as st

from pages.utils import Scrapper, Db

st.header("Create job collection")


# col1, col2 = st.columns(2)

scrapper = Scrapper()


@st.cache_data
def departement():
    return scrapper.query(endpoint="/referentiel/departements").json()


with st.sidebar:
    with st.form("run", border=False):
        deps = departement()
        departement = st.selectbox("Département", [d["code"] for d in deps],
                                   format_func=lambda x: [d["libelle"] for d in deps if d["code"] == x][0])
        limit = st.slider("Limit", 1, 10000, 10)
        collection = st.text_input("Collection")
        st.write("Or select an existing collection")
        selected_collection = st.selectbox("Collection", Db.get_collections("jobs"))
        if st.form_submit_button("Run"):
            scrapper.db = Db.get_db("jobs", collection or selected_collection)
            scrapper.run(parameters={"departement": departement}, limit=limit)
