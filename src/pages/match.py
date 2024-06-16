import streamlit as st

from pages.utils import Db, Scrapper

st.header("Search job")

with st.sidebar:
    with st.form("run", border=False):
        experience_text = st.text_area("Experience", height=100)
        vocab_collections = st.multiselect("Vocab Collections", Db.get_collections("vocab"))
        jobs_collections = st.multiselect("Jobs Colections", Db.get_collections("jobs"))
        if st.form_submit_button("Run"):
            st.session_state["jobs_collections"] = jobs_collections
            st.session_state["vocab_collections"] = vocab_collections
            st.session_state["vocab"] = Db.get_ids("vocab", vocab_collections)
            st.session_state["experience_doc"] = Scrapper.find_keywords({"description": experience_text, "intitule": ""}, st.session_state["vocab"])
            docs = []
            for document in Db.get_documents("jobs", jobs_collections):
                document["score"] = Scrapper.score_matching(document, st.session_state["experience_doc"],
                                                            st.session_state["vocab"])
                docs.append(document)
            st.session_state["documents"] = sorted(docs, key=lambda x: x["score"], reverse=True)
            st.write(st.session_state["experience_doc"])
limit = st.slider("Limit", 1, 100, 10)
if st.session_state.get("documents"):
    st.subheader("Results")
    for document in st.session_state["documents"][:limit]:
        st.write(document)






