import os
from dotenv import load_dotenv
import pymongo
import openai
import pprint
import streamlit as st

from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

load_dotenv(override=True)

# Initialize OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY


# MongoDB setup
MONGO_DB_URI = str(os.getenv("MONGO_DB_URI"))
MONGO_DB_NAME = str(os.getenv("MONGO_DB_NAME"))
MONGO_COLLECTION_NAME = str(os.getenv("MONGO_COLLECTION_NAME"))

mongo = pymongo.MongoClient(MONGO_DB_URI)
db = mongo[MONGO_DB_NAME]
atlas_collection = db[MONGO_COLLECTION_NAME]
vector_search_index = "vector_index"

rag_chain: any
retriever: any

def create_chunks():
    if not st.session_state.transcript:
            return []
    
    # Split text into documents using RecursiveCharacterTextSplitter
    doc = Document(page_content=st.session_state.transcript)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
    docs = text_splitter.split_documents([doc])

    # Print the first document
    docs[0]

    return docs

def create_vector_store(docs):
    # Create the vector store
    vector_search = MongoDBAtlasVectorSearch.from_documents(
        documents = docs,
        embedding = OpenAIEmbeddings(disallowed_special=()),
        collection = atlas_collection,
        index_name = vector_search_index
    )
    return vector_search

def query_vector_store(vector_store, query):
    results = vector_store.similarity_search(query)
    pprint.pprint(results)

def build_rag_chain(vector_store):
    # Instantiate Atlas Vector Search as a retriever
    retriever = vector_store.as_retriever(
        search_type = "similarity",
        search_kwargs = {"k": 10, "score_threshold": 0.75}
    )

    # Define a prompt template
    template = """

    Use the following pieces of context to answer the question at the end.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.

    {context}

    Question: {question}
    """
    custom_rag_prompt = PromptTemplate.from_template(template)

    llm = ChatOpenAI(temperature=0.1)

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # Construct a chain to answer questions on your data
    rag_chain = (
        { "context": retriever | format_docs, "question": RunnablePassthrough()}
        | custom_rag_prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain, retriever

def query_rag_chain(rag_chain, retriever, question):
    # Prompt the chain
    answer = rag_chain.invoke(question)

    print("Question: " + question)
    print("Answer: " + answer)

    # Return source documents
    documents = retriever.get_relevant_documents(question)
    print("\nSource documents:")
    pprint.pprint(documents)
    return answer

def invoke_rag_chain(query):
    docs = create_chunks()
    vector_store = create_vector_store(docs)
    query_vector_store(vector_store, query) # Can skip, just querying
    rag_chain, retriever = build_rag_chain(vector_store)
    answer = query_rag_chain(rag_chain, retriever, query)
    return answer

