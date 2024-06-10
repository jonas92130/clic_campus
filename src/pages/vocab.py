import streamlit as st

from pages.utils import Db

st.header("Create vocabulary collection")


def set_data():
    st.session_state["vocab_data"] = Db.get_ids("vocab", [st.session_state["vocab_collection"]])
    st.session_state["stopwords_data"] = Db.get_ids("vocab", st.session_state["stopwords_collections"])
    st.session_state["counters"] = Db.get_counters(collections, remove_words=(st.session_state["vocab_data"] +
                                                                              st.session_state["stopwords_data"]))
    st.rerun()


with st.sidebar:
    with st.form("run", border=False):
        collections = st.multiselect("Job Collections", Db.get_collections("jobs"))
        vocab_collection = st.text_input("Vocabulary Collection", )
        selected_collection = st.selectbox("Or select an existing collection", Db.get_collections("vocab"))
        stopword_collections = st.multiselect("Stopwords Collections", Db.get_collections("vocab"))
        if st.form_submit_button("Run"):
            st.session_state["stopwords_collections"] = stopword_collections
            st.session_state["vocab_collection"] = vocab_collection or selected_collection
            set_data()

col1, col2 = st.columns(2, gap="large")
with col1:
    if st.session_state.get("vocab_data"):
        collection = st.session_state["vocab_collection"]
        st.subheader(f"Vocabulary {collection}")
        select_all = st.checkbox("Select All", value=True)
        with st.form('vocab_form'):
            checkboxes = []
            with st.container(height=500, border=False):
                for word in st.session_state["vocab_data"]:
                    checkboxes.append((st.checkbox(f"{word}", value=select_all), word))
            if st.form_submit_button("Save", type="primary"):
                db = Db.get_db("vocab", collection)
                db.remove_ids([word for checked, word in checkboxes if not checked])
                set_data()
        # st.write(data)
with col2:
    if st.session_state.get("counters"):
        st.subheader("Jobs keywords")
        counters = st.session_state["counters"]
        nb_values = st.slider("Top", 1, 1000, 100)
        option = st.selectbox('POS', ["ALL"] + [c for c in counters if c != "ALL"])
        select_all = st.checkbox("Select All", value=True, key="words_select_all")
        with st.form('words_form'):
            # for name, counter in counters.items():
            #     for word in st.session_state["vocabulary"]:
            #         counter.pop(word, None)
            checkboxes = []
            with st.container(height=500, border=False):
                for word, count in counters[option].most_common(nb_values):
                    checkboxes.append((st.checkbox(f"{word} ({count})", value=select_all), word))
            st.write(st.session_state["vocab_collection"])
            if st.form_submit_button('Add to my vocabulary', type="primary"):
                db = Db.get_db("vocab", st.session_state["vocab_collection"] or
                               st.session_state["vocab_collections"])
                db.insert(({"_id": word} for checked, word in checkboxes if checked))
                set_data()
