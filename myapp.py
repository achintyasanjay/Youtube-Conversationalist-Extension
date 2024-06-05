# import streamlit as st
# import yt_dlp
# import imageio_ffmpeg as iof

# def download_audio(video_url):
#     ydl_opts = {
#         'format': 'bestaudio/best',
#         'postprocessors': [{
#             'key': 'FFmpegExtractAudio',
#             'preferredcodec': 'mp3',
#             'preferredquality': '192',
#         }],
#         'ffmpeg_location': iof.get_ffmpeg_exe(),
#         'outtmpl': 'downloads/%(title)s.%(ext)s',  # Directory and filename template
#     }

#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         info_dict = ydl.extract_info(video_url, download=True)
#         video_title = info_dict.get('title', None)
#         return video_title

# def main():
#     st.title('Video Conversationalist')

#     # video_url = st.text_input('Enter YouTube Video URL:', '')
#     query_params = st.experimental_get_query_params()

#     st.write("Query parameters:", query_params)  # Log the query parameters

#     video_url = query_params.get('video_url', [None])[0]
#     st.write("Video URL:", video_url)  # Log the video URL

#     if video_url:
#         try:
#             video_title = download_audio(video_url)
#             if video_title:
#                 st.success(f'Audio downloaded successfully: {video_title}.mp3')
#             else:
#                 st.error('Failed to download audio. Check the video URL.')
#         except Exception as e:
#             st.error(f'An error occurred: {str(e)}')
#     else:
#         st.write('Please provide a YouTube video URL.')

# if __name__ == '__main__':
#     main()
import os
import streamlit as st
import yt_dlp
import imageio_ffmpeg as iof
from vectorizeAudio import vectorize_audio, get_transcript
import openai
from dotenv import load_dotenv
import pymongo

load_dotenv(override=True)

# # Initialize OpenAI
# openai_api_key = os.getenv("openai_api_key")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# MongoDB setup
MONGO_DB_URI = os.getenv("MONGO_DB_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME")

mongo = pymongo.MongoClient(MONGO_DB_URI)
db = mongo[MONGO_DB_NAME]
collection = db[MONGO_COLLECTION_NAME]

video_title = None
transcript = None

def download_audio(video_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        # 'ffmpeg_location': iof.get_ffmpeg_exe(),
        'ffmpeg_location': "/opt/homebrew/bin/ffmpeg",
        'outtmpl': 'downloads/%(title)s.%(ext)s',  # Directory and filename template
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
        video_title = info_dict.get('title', None)
        return video_title




def query_openai(question, documents):
    if documents:
        context = " ".join(documents)
        full_prompt = f"Answer the following question based on the documents provided: {question}\n\n{context}"
    else:
        full_prompt = f"No relevant information found in the vector database. Nevertheless, here's a response based on general knowledge: {question}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
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
        documents = transcript
        return [doc['data'] for doc in documents]
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return []

# Function to handle summary generation
def generate_summary(transcript):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
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


def main():
    st.title('YouTube Conversationalist')

    video_title = None
    transcript = None

    video_url = st.text_input('Enter YouTube Video URL:', '')

    if st.button('Pass Youtube URL'):
        if video_url:
            try:
                video_title = download_audio(video_url)
                if video_title:
                    st.success(f'Audio downloaded successfully: {video_title}.mp3')

                    # save audio file in vector db
                    vectorize_audio(video_title, f"./downloads/{video_title}.mp3")
                    
                else:
                    st.error('Failed to download audio. Check the video URL.')
            except Exception as e:
                st.error(f'An error occurred: {str(e)}')
        else:
            st.error('Please enter a valid YouTube video URL.')
    
    if video_title:
        transcript = get_transcript(video_title, f"./downloads/{video_title}.mp3")
        print(transcript)

    tab1, tab2 = st.tabs(["Summary", "Chat"])

    with tab1:
        st.header("Video Summary")
        if transcript:
            summary = generate_summary(transcript)
            st.write(summary)

    with tab2:
        st.header("Chat with RAG")
        # Input field with on_change callback for chat
        st.text_input("Ask a question:", key="user_query", on_change=handle_query)
        # Display the conversation history
        for message in st.session_state.conversation:
            st.text(message)

def handle_query():
    user_query = st.session_state.user_query
    if user_query:  # Check if there is a query
        # documents = get_related_documents(user_query)
        response = query_openai(user_query, transcript)
        # Append both user query and bot response to the conversation
        st.session_state.conversation.append(f"User: {user_query}")
        st.session_state.conversation.append(f"Bot: {response}")
        # Clear the input after processing
        st.session_state.user_query = ""

# Initialize session state for conversation
if 'conversation' not in st.session_state:
    st.session_state.conversation = []

if __name__ == '__main__':
    main()