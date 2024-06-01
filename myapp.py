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
import streamlit as st
import yt_dlp
import imageio_ffmpeg as iof

def download_audio(video_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'ffmpeg_location': iof.get_ffmpeg_exe(),
        'outtmpl': 'downloads/%(title)s.%(ext)s',  # Directory and filename template
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
        video_title = info_dict.get('title', None)
        return video_title

def main():
    st.title('YouTube Audio Downloader')

    video_url = st.text_input('Enter YouTube Video URL:', '')

    if st.button('Download Audio'):
        if video_url:
            try:
                video_title = download_audio(video_url)
                if video_title:
                    st.success(f'Audio downloaded successfully: {video_title}.mp3')
                else:
                    st.error('Failed to download audio. Check the video URL.')
            except Exception as e:
                st.error(f'An error occurred: {str(e)}')
        else:
            st.error('Please enter a valid YouTube video URL.')

if __name__ == '__main__':
    main()