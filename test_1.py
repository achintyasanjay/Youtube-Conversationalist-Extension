import streamlit as st
from pymongo import MongoClient
from openai import OpenAI

OPENAI_API_KEY = "enter key"
openai_client = OpenAI(api_key=OPENAI_API_KEY)
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import OpenAIEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
# Initialize OpenAI
# OPENAI_API_KEY = st.secrets["openai_api_key"]

# MongoDB setup
connection_string = "enter connection string"
client = MongoClient(connection_string)
print(client)
db = client['langchain_chatbot']
collections = db.list_collection_names()
print(collections)
transcripts_collection = db.data
sample_documents = transcripts_collection.find().limit(2)

DB_NAME = "langchain_chatbot"
COLLECTION_NAME = "data"
ATLAS_VECTOR_SEARCH_INDEX_NAME = "vector_index"
collection = client[DB_NAME][COLLECTION_NAME]

embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model="text-embedding-ada-002")

# Vector Store Creation
vector_store = MongoDBAtlasVectorSearch.from_connection_string(
    connection_string=connection_string,
    namespace=DB_NAME + "." + COLLECTION_NAME,
    embedding= embeddings,
    index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
    text_key="fullplot"
)
retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})

# Generate context using the retriever, and pass the user question through
retrieve = {"context": retriever | (lambda docs: "\n\n".join([d.page_content for d in docs])), "question": RunnablePassthrough()}
template = """Answer the question based only on the following context: \
{context}

Question: {question}
"""
# Defining the chat prompt
prompt = ChatPromptTemplate.from_template(template)
# Defining the model to be used for chat completion
model = ChatOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
# Parse output as a string
parse_output = StrOutputParser()


# Naive RAG chain 
naive_rag_chain = (
    retrieve
    | prompt
    | model
    | parse_output
)

def query_openai(question, documents):
    if documents:
        context = " ".join(documents)
        full_prompt = f"Answer the following question based on the documents provided: {question}\n\n{context}"
    else:
        full_prompt = f"No relevant information found in the vector database. Nevertheless, here's a response based on general knowledge: {question}"
    response = openai_client.chat.completions.create(model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": full_prompt}
    ],
    max_tokens=150)
    return response.choices[0].message.content


# Function to get related documents from MongoDB
def get_related_documents(query):

    try:
      naive_rag_chain.invoke("ice cream flavours mentioned in the document")
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return []

# Function to handle summary generation
def generate_summary(transcript):
    response = openai_client.chat.completions.create(model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": transcript}
    ],
    max_tokens=1500)
    # Properly access the 'content' of the response
    return response.choices[0].message.content

# Function to query OpenAI with chat
# Function to handle chat queries and update the conversation
def handle_query():
    user_query = st.session_state.user_query
    if user_query:  # Check if there is a query
        documents = get_related_documents(user_query)
        response = query_openai(user_query, documents)
        # Append both user query and bot response to the conversation
        st.session_state.conversation.append(f"User: {user_query}")
        st.session_state.conversation.append(f"Bot: {response}")
        # Clear the input after processing
        st.session_state.user_query = ""

# Initialize session state for conversation
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
# Main application layout
def main():
    st.title("YouTube Video Processor and Chatbot")

    # Assume transcript is automatically updated from an external source
    transcript = "Your automatically fetched transcript goes here."

    # Create tabs
    tab1, tab2 = st.tabs(["Summary", "Chat"])

    with tab1:
        st.header("Video Summary")
        summary = generate_summary(transcript)
        st.write(summary)

    with tab2:
        st.header("Chat with RAG")
        # Input field with on_change callback for chat
        st.text_input("Ask a question:", key="user_query", on_change=handle_query)
        # Display the conversation history
        for message in st.session_state.conversation:
            st.text(message)

if __name__ == "__main__":
    main()
