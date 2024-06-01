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
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain import hub

load_dotenv()
DG_API_KEY = os.getenv("DG_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# URL to the audio file
AUDIO_FILE = "/Users/subrahmanyam.arunachalam/Downloads/Manchester-City-vs-Real-Madrid-5-6-Peter-Drury-Commentary-Full-Highlights.mp3"

try:
    # STEP 1 Create a Deepgram client using the API key
    deepgram = DeepgramClient(DG_API_KEY)

    #STEP 2: Configure Deepgram options for audio analysis
    options = PrerecordedOptions(
        model="nova-2",
        smart_format=True,
    )

    with open(AUDIO_FILE, "rb") as file:
            buffer_data = file.read()

    payload: FileSource = {
        "buffer": buffer_data,
    }


    # STEP 3: Call the transcribe_file method with the text payload and options
    response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)
    # STEP 4: Print the response
    print(response.to_json(indent=4))

except Exception as e:
    print(f"Exception: {e}")

with open('dataset.txt', 'w') as f:
    f.write(response['results'].channels[0].alternatives[0].transcript)


model_name = "BAAI/bge-small-en"
model_kwargs = {"device": "cpu"}
encode_kwargs = {"normalize_embeddings": True}
hf = HuggingFaceBgeEmbeddings(
    model_name=model_name, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs
)

# Load the document, split it into chunks, embed each chunk and load it into the vector store.
raw_documents = TextLoader('dataset.txt').load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
documents = text_splitter.split_documents(raw_documents)
db = FAISS.from_documents(documents, hf)
retriever = db.as_retriever()

# Query the vector store with a query document
query = "tell me about your second love story"
docs = db.similarity_search(query)
print(docs[0].page_content)

llm = ChatGroq(temperature=0, model_name="llama3-70b-8192")
prompt = hub.pull("rlm/rag-prompt")
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

print(rag_chain.invoke(query))

