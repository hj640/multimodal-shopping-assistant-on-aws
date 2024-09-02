import streamlit as st 
from streamlit_js_eval import streamlit_js_eval
# from langchain.callbacks import StreamlitCallbackHandler
import utils as util
from datetime import datetime
import uuid 

def get_or_create_session_id():
    if "session_id" not in st.session_state: 
        st.session_state["session_id"] = str(uuid.uuid4())
    return st.session_state["session_id"]

def start_new_chat():
    st.session_state["session_id"] = str(uuid.uuid4())
    st.session_state["messages"] = [
        {"role": "assistant",
         "content": "Hi, I'm your fashion assistant bot. Before we start, may I get your customer name?"}
    ]

def show_multimodal_answer(response):
    with st.chat_message("assistant"):
        for img, desc in response:
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(img, caption="")
            with col2:
                st.write(desc)

###### APPLICATION UI/UX VIEW ######

st.set_page_config(layout="wide")
st.title("Fashion Assistant Bot")

session_id = get_or_create_session_id()

if st.button("Start New Chat"):
    start_new_chat()
    session_id = get_or_create_session_id()

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant",
         "content": "Hi, I'm your fashion assistant bot. Before we start, may I get your customer name?"}
    ]

for msg in st.session_state.messages:
    if msg["role"] == "assistant" or msg["role"] == "user":
        st.chat_message(msg["role"]).write(msg["content"])
    else:
        response = msg["content"]
        show_multimodal_answer(response)

prompt = st.chat_input("")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    multi_modal, answer = util.query(prompt=prompt, session_id=st.session_state["session_id"])
    print("RECEIVED ANSWER: ", answer)
    if multi_modal: 
        with st.chat_message("assistant"):
            for img, desc in answer: 
                col1, col2 = st.columns([1, 3])
                with col1: 
                    st.image(img, caption="")
                with col2:
                    st.write(desc)
        st.session_state.messages.append({"role": "multi-modal-assistant", "content": answer})
    else:
        with st.chat_message("assistant"):
            st.write(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})