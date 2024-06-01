import streamlit as st
from pymongo import MongoClient
import openai

# Initialize OpenAI
openai_api_key = 'sk-proj-8mT1N02DGCyjB2f5k767T3BlbkFJwv5rc1rmHzv4S2vQtTw5'
openai.api_key = openai_api_key

# MongoDB setup
connection_string = "mongodb+srv://mukulm2010:h1VLOWHWMUMS5RYT@cluster0.7ruqy85.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
try:
    # Connect to MongoDB
    mongo_client = MongoClient(connection_string)
    # Access the specific database
    db = mongo_client['langchain_chatbot']
    # Example operation: list collections
    print(db.list_collection_names())
except Exception as e:
    print(f"An error occurred while connecting to MongoDB: {e}")# Function definitions
def get_related_documents(query):
    try:
        # MongoDB setup
        mongo_client = MongoClient("your_mongodb_connection_string", serverSelectionTimeoutMS=5000)
        db = mongo_client.your_database_name
        transcripts_collection = db.transcripts
        documents = transcripts_collection.find({"$text": {"$search": query}})
        return [doc['transcript'] for doc in documents]
    except Exception as e:
        print(f"Database connection failed: {e}")
        return []  # Return an empty list if MongoDB fails

def query_openai(question, documents):
    if documents:
        context = " ".join(documents)
        full_prompt = f"Answer the following question based on the documents provided: {question}\n\n{context}"
    else:
        full_prompt = f"No relevant information found in the vector database. Nevertheless, here's a response based on general knowledge: {question}"
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": full_prompt}
        ],
        max_tokens=150
    )
    return response['choices'][0]['message']['content']

# Initialize session state for conversation
if 'conversation' not in st.session_state:
    st.session_state.conversation = []

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

st.title('RAG Chatbot')

# Input field with on_change callback
user_query = st.text_input("Ask a question:", key="user_query",
                           on_change=handle_query, args=())

# Display the conversation history
for message in st.session_state.conversation:
    st.text(message)