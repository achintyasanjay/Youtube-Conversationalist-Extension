import os
from dotenv import load_dotenv
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource
)
import together
import pymongo
from typing import List

load_dotenv(override=True)

DG_API_KEY = os.getenv("DG_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
together.api_key = TOGETHER_API_KEY
MONGO_DB_URI = os.getenv("MONGO_DB_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME")
MODEL = os.getenv("MODEL")

def generate_embeddings(input_texts: List[str], model_api_string: str) -> List[List[float]]:
    """Generate embeddings from Together python library.

    Args:
        input_texts: a list of string input texts.
        model_api_string: str. An API string for a specific embedding model of your choice.

    Returns:
        embeddings_list: a list of embeddings. Each element corresponds to the each input text.
    """
    try:
        together_client = together.Together()
        outputs = together_client.embeddings.create(
            input=input_texts,
            model=model_api_string,
        )
        return [x.embedding for x in outputs.data]
    except Exception as e:
        print(f"Exception: {e}")

def store_embeddings(video_title: str, embedding: List[float]):
    """Store the input text and its corresponding embedding into MongoDB.

    Args:
        video_title: str. the youtube video title.
        embedding: List[float]. list of embeddings.
    """
    try:
        mongo = pymongo.MongoClient(MONGO_DB_URI)
        db = mongo[MONGO_DB_NAME]
        collection = db[MONGO_COLLECTION_NAME]
        
        document = {
            "text": video_title,
            "embedding": embedding
        }
        
        collection.insert_one(document)
    except Exception as e:
        print(f"Exception: {e}")

def store_text(video_title: str, text: str):
    """Store the input text and its corresponding embedding into MongoDB.

    Args:
        video_title: str. the youtube video title.
        embedding: List[float]. list of embeddings.
    """
    try:
        mongo = pymongo.MongoClient(MONGO_DB_URI)
        db = mongo[MONGO_DB_NAME]
        collection = db[MONGO_COLLECTION_NAME]

        document = {
            "title": video_title,
            "raw_text": text
        }
        
        collection.insert_one(document)
    except Exception as e:
        print(f"Exception: {e}")

def vectorize_audio(video_title: str, audio_file):
    """vectorize an audio file into mongodb atlas.

    Args:
        video_title: str. the youtube video title.
        audio_file: str. path to the audio file.

    Returns:
        embeddings_list: a list of embeddings. Each element corresponds to the each input text.
    """
    try:
        deepgram = DeepgramClient(DG_API_KEY)

        options = PrerecordedOptions(
            model="nova-2",
            smart_format=True,
        )

        with open(audio_file, "rb") as file:
            buffer_data = file.read()

        payload: FileSource = {
            "buffer": buffer_data,
        }

        # transcribing the audio
        response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)

        # Vectorizing the transcription
        embeddings = generate_embeddings([response["results"]["channels"][0]["alternatives"][0]["transcript"]], MODEL)
        store_embeddings(video_title, embeddings[0])
        # store_text(video_title, response["results"]["channels"][0]["alternatives"][0]["transcript"])

    except Exception as e:
        print(f"Exception: {e}")

def get_transcript(video_title: str, audio_file):
    deepgram = DeepgramClient(DG_API_KEY)

    options = PrerecordedOptions(
        model="nova-2",
        smart_format=True,
    )

    with open(audio_file, "rb") as file:
        buffer_data = file.read()

    payload: FileSource = {
        "buffer": buffer_data,
    }

    # transcribing the audio
    response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)

    return response["results"]["channels"][0]["alternatives"][0]["transcript"]