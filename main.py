import streamlit as st
from pymongo import MongoClient
import openai
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize OpenAI
# openai_api_key = st.secrets["openai_api_key"]
openai_api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = openai_api_key

# MongoDB setup
connection_string = "enter api string here"
mongo_client = MongoClient(connection_string)
db = mongo_client['langchain_chatbot']
transcripts_collection = db.data


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


# Function to get related documents from MongoDB
def get_related_documents(query):
    try:
        # Ensure a text index exists on the 'transcript' field, or MongoDB won't be able to execute a text search.
        print(query)
        documents = transcripts_collection.find({"$text": {"$search": query}})
        return [doc['data'] for doc in documents]
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return []

# Function to handle summary generation
def generate_summary(transcript):
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": transcript}
        ],
        max_tokens=1500
    )
    # Properly access the 'content' of the response
    return response['choices'][0]['message']['content']

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