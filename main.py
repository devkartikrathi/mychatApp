import streamlit as st
from openai.error import OpenAIError

def faq():
    st.markdown(
        """
# FAQ
## How does mychatApp work?
When you upload a document, it will be divided into smaller chunks 
and stored in a special type of database called a vector index 
that allows for semantic search and retrieval.

When you ask a question, mychatApp will search through the
document chunks and find the most relevant ones using the vector index.
Then, it will use GPT3 to generate a final answer.

## Is my data safe?
Yes, your data is safe. mychatApp does not store your documents or
questions. All uploaded data is deleted after you close the browser tab.

## Why does it take so long to index my document?
If you are using a free OpenAI API key, it will take a while to index
your document. This is because the free API key has strict [rate limits](https://platform.openai.com/docs/guides/rate-limits/overview).
To speed up the indexing process, you can use a paid API key.

## What do the numbers mean under each source?
For a PDF document, you will see a citation number like this: 3-12. 
The first number is the page number and the second number is 
the chunk number on that page. For DOCS and TXT documents, 
the first number is set to 1 and the second number is the chunk number.

## Are the answers 100% accurate?
No, the answers are not 100% accurate. mychatApp uses GPT-3 to generate
answers. GPT-3 is a powerful language model, but it sometimes makes mistakes 
and is prone to hallucinations. Also, mychatApp uses semantic search
to find the most relevant chunks and does not see the entire document,
which means that it may not be able to find all the relevant information and
may not be able to answer all questions (especially summary-type questions
or questions that require a lot of context from the document).

But for most use cases, mychatApp is very accurate and can answer
most questions. Always check with the sources to make sure that the answers
are correct.
"""
    )

from utils import (
    embed_docs,
    get_answer,
    get_sources,
    parse_docx,
    parse_pdf,
    parse_txt,
    search_docs,
    text_to_docs,
    wrap_text_in_html,
)


def set_openai_api_key(api_key: str):
    st.session_state["OPENAI_API_KEY"] = api_key
    
def clear_submit():
    st.session_state["submit"] = False


def sidebar():
    with st.sidebar:
        st.markdown(
            "## How to use\n"
            "1. Enter your [OpenAI API key](https://platform.openai.com/account/api-keys) below🔑\n"  # noqa: E501
            "2. Upload a pdf, docx, or txt file📄\n"
            "3. Ask a question about the document💬\n"
        )
        api_key_input = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="Paste your OpenAI API key here (sk-...)",
            help="You can get your API key from https://platform.openai.com/account/api-keys.",  # noqa: E501
            value=st.session_state.get("OPENAI_API_KEY", ""),
        )

        if api_key_input:
            set_openai_api_key(api_key_input)

        st.markdown("---")
        st.markdown("# About")
        st.markdown(
            "mychatApp allows you to ask questions about your "
            "documents and get accurate answers with instant citations. "
        )
        st.markdown(
            "This tool is a work in progress. "
            "You can contribute to the project on [GitHub](https://github.com/shivashishbhardwaj/mychatApp) "  # noqa: E501
            "with your feedback and suggestions💡"
        )
        st.markdown("Made by [Shiva]")
        st.markdown("---")

        faq()
st.set_page_config(page_title="Chat with your Doc", page_icon="📖", layout="wide")
st.header("📖 My ChatApp")

sidebar()
        
uploaded_file = st.file_uploader(
    "Upload a pdf, docx, or txt file",
    type=["pdf", "docx", "txt"],
    help="Scanned documents are not supported yet!",
    on_change=clear_submit)

index = None
doc = None
if uploaded_file is not None:
    if uploaded_file.name.endswith(".pdf"):
        doc = parse_pdf(uploaded_file)
    elif uploaded_file.name.endswith(".docx"):
        doc = parse_docx(uploaded_file)
    elif uploaded_file.name.endswith(".txt"):
        doc = parse_txt(uploaded_file)
    else:
        raise ValueError("File type not supported!")
    text = text_to_docs(doc)
    try:
        with st.spinner("Indexing document... This may take a while⏳"):
            index = embed_docs(text)
        st.session_state["api_key_configured"] = True
    except OpenAIError as e:
        st.error(e._message)

query = st.text_area("Ask a question about the document", on_change=clear_submit)
with st.expander("Advanced Options"):
    show_all_chunks = st.checkbox("Show all chunks retrieved from vector search")
    show_full_doc = st.checkbox("Show parsed contents of the document")

if show_full_doc and doc:
    with st.expander("Document"):
        # Hack to get around st.markdown rendering LaTeX
        st.markdown(f"<p>{wrap_text_in_html(doc)}</p>", unsafe_allow_html=True)

button = st.button("Submit")
if button or st.session_state.get("submit"):
    if not st.session_state.get("api_key_configured"):
        st.error("Please configure your OpenAI API key!")
    elif not index:
        st.error("Please upload a document!")
    elif not query:
        st.error("Please enter a question!")
    else:
        st.session_state["submit"] = True
        # Output Columns
        answer_col, sources_col = st.columns(2)
        sources = search_docs(index, query)

        try:
            answer = get_answer(sources, query)
            if not show_all_chunks:
                # Get the sources for the answer
                sources = get_sources(answer, sources)

            with answer_col:
                st.markdown("#### Answer")
                st.markdown(answer["output_text"].split("SOURCES: ")[0])

            with sources_col:
                st.markdown("#### Sources")
                for source in sources:
                    st.markdown(source.page_content)
                    st.markdown(source.metadata["source"])
                    st.markdown("---")

        except OpenAIError as e:
            st.error(e._message)


hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
