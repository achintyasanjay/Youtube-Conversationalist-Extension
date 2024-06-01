import streamlit as st
from st_audiorec import st_audiorec
import os
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
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

st.title("Personal affirmations")

def get_vectorstore(text_chunks):
    try:
      model_name = "BAAI/bge-small-en"
      model_kwargs = {"device": "cpu"}
      encode_kwargs = {"normalize_embeddings": True}
      hf = HuggingFaceBgeEmbeddings(
          model_name=model_name, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs
      )

      # Load the document, split it into chunks, embed each chunk and load it into the vector store.
      db = FAISS.from_documents(text_chunks, hf)
      return db
    except Exception as e:
        print(e)
        print(text_chunks)


def get_conversation_chain(vectorstore):
    llm = ChatGroq(temperature=0, model_name="llama3-70b-8192")
    memory = ConversationBufferMemory(memory_key="chat_history", return_source_documents=True, return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )
    return conversation_chain

def handle_userinput(user_question):
    bot_template = "BOT : {0}"
    user_template = "USER : {0}"
    try:
        response = st.session_state.conversation({'question': user_question})
        print("Response", response)
    except ValueError as e:
        st.write(e)
        st.write("Sorry, please ask again in a different way.")
        return
    st.session_state.chat_history = response['chat_history']
    # Clear the content of the chat window
    # st.write(user_template.replace("{0}", response['question']))
    # st.write(bot_template.replace("{0}", response['answer']))
    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace("{0}", message.content))
        else:
            st.write(bot_template.replace("{0}", message.content))
            audio_file_path = "/Users/subrahmanyam.arunachalam/Downloads/Manchester-City-vs-Real-Madrid-5-6-Peter-Drury-Commentary-Full-Highlights.mp3"  # Replace this with your actual file path

            # Display the audio file
            st.audio(audio_file_path, format="audio/mp3")

wav_audio_data = st_audiorec()

if wav_audio_data is not None:
    st.audio(wav_audio_data, format='audio/wav')

mp3_docs = st.file_uploader("Upload your MP3 here and click on 'Process'", type=['mp3', 'wav'], accept_multiple_files=False)
if st.button("Process"):
    with st.spinner("Processing"):
        try:
        # STEP 1 Create a Deepgram client using the API key
          deepgram = DeepgramClient(DG_API_KEY)

          #STEP 2: Configure Deepgram options for audio analysis
          options = PrerecordedOptions(
              model="nova-2",
              smart_format=True,
          )

          # with open(mp3_docs, "rb") as file:
          #         buffer_data = file.read()

          payload: FileSource = {
              "buffer": mp3_docs,#buffer_data,
          }


          # STEP 3: Call the transcribe_file method with the text payload and options
          response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)
          # STEP 4: Print the response
          print(response.to_json(indent=4))

        except Exception as e:
            print(f"Exception: {e}")

        with open('dataset.txt', 'w') as f:
            f.write(response['results'].channels[0].alternatives[0].transcript)
        
        raw_documents = TextLoader('dataset.txt').load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        documents = text_splitter.split_documents(raw_documents)
        vectorstore = get_vectorstore(documents)
        st.session_state.conversation = get_conversation_chain(vectorstore)


if "conversation" not in st.session_state:
    try:
        st.session_state.conversation = get_conversation_chain(get_vectorstore(None))
    except:
        st.write("Upload your audio file...")
        st.stop()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = None

user_question = st.text_input("Ask a question about your documents:")
if user_question:
    handle_userinput(user_question)
    st.empty()