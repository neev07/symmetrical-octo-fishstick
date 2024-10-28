from flask import Flask, render_template, request, redirect, url_for
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import yt_dlp
import requests

app = Flask(__name__)

# Spotify API credentials
CLIENT_ID = "e5af495b89134e06a025170ab808d527"
CLIENT_SECRET = "d89e779ff0624afb854457c16ec12203"
REDIRECT_URI = 'http://localhost:8888/callback'

# YouTube API Key
YOUTUBE_API_KEY = 'AIzaSyBfcbDS_JdWy-AYOetUu6_j9nbHc_aWgiY' 

# Set up Spotify API authentication
scope = 'playlist-read-private'
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope=scope))

# Route to the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Function to fetch playlist songs and download from YouTube
@app.route('/download', methods=['POST'])
def download():
    playlist_link = request.form['playlist_url']
    playlist_URI = playlist_link.split("/")[-1].split("?")[0]
    songs = []
    youtube_links = []

    # Fetch playlist tracks
    def get_playlist_tracks(sp, playlist_id):
        results = sp.playlist_tracks(playlist_id)
        tracks = results['items']
        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])
        return tracks

    def search_youtube_data_api(song):
        query = f"{song['title']} {song['artist']}"
        url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={YOUTUBE_API_KEY}&maxResults=1&type=video'
        response = requests.get(url)
        if response.status_code == 200:
            results = response.json()
            if results['items']:
                return f"https://www.youtube.com/watch?v={results['items'][0]['id']['videoId']}"
        return None

    # Display playlist info and populate songs list
    try:
        tracks = get_playlist_tracks(sp, playlist_URI)
        for item in tracks:
            track = item['track']
            songs.append({"title": track['name'], "artist": track['artists'][0]['name']})

        for song in songs:
            link = search_youtube_data_api(song)
            youtube_links.append(link)

        download_dir = "downloaded_songs"
        os.makedirs(download_dir, exist_ok=True)

        def download_audio(youtube_url):
            try:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'extractaudio': True,
                    'audioformat': 'mp3',
                    'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([youtube_url])
            except Exception as e:
                print(f"Error downloading {youtube_url}: {e}")

        for link in youtube_links:
            download_audio(link)

    except Exception as e:
        return f"An error occurred: {e}"

    return "Songs downloaded successfully!"

if __name__ == '__main__':
    app.run(debug=True)
