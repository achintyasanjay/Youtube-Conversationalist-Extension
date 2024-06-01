import os
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource
)
from langchain_community.document_loaders import TextLoader
# from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
# from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain import hub
import together
import pymongo
from typing import List

load_dotenv()
DG_API_KEY = os.getenv("DG_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
together.api_key = TOGETHER_API_KEY
MONGO_DB_URI = os.getenv("MONGO_DB_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME")

AUDIO_FILE = "./testing-audio/ice-cream.m4a"
TITLE = "test youtube video title"

EMBEDDING = "meta-llama/Llama-2-70b-chat-hf"

def generate_embeddings(input_texts: List[str], model_api_string: str) -> List[List[float]]:
    """Generate embeddings from Together python library.

    Args:
        input_texts: a list of string input texts.
        model_api_string: str. An API string for a specific embedding model of your choice.

    Returns:
        embeddings_list: a list of embeddings. Each element corresponds to the each input text.
    """
    together_client = together.Together()
    outputs = together_client.embeddings.create(
        input=input_texts,
        model=model_api_string,
    )
    return [x.embedding for x in outputs.data]

def store_embeddings(video_title: str, embedding: List[float]):
    """Store the input text and its corresponding embedding into MongoDB."""
    # Connect to MongoDB
    mongo = pymongo.MongoClient(MONGO_DB_URI)
    db = mongo.MONGO_DB_NAME
    collection = db.MONGO_COLLECTION_NAME
    
    document = {
        "text": video_title,
        "embedding": embedding
    }
    
    collection.insert_one(document)

try:
    deepgram = DeepgramClient(DG_API_KEY)

    # transcribing the audio

    options = PrerecordedOptions(
        model="nova-2",
        smart_format=True,
    )

    with open(AUDIO_FILE, "rb") as file:
            buffer_data = file.read()

    payload: FileSource = {
        "buffer": buffer_data,
    }

    response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)

    # Vectorizing the transcription
    output = generate_embeddings([response], EMBEDDING)
    print(f"Embedding size is: {str(len(output[0]))}")

except Exception as e:
    print(f"Exception: {e}")
