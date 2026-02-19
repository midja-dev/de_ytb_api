import requests
import json
import os
from dotenv import load_dotenv


load_dotenv(dotenv_path="./.env")
API_KEY = os.getenv("API_KEY")
CHANNEL_HANDLE = "MrBeast"
MAX_RESULTS = 50  # max retries for videos IDs API calls

def get_playlist_id():

    try:

        url = f"https://youtube.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={CHANNEL_HANDLE}&key={API_KEY}"

        response = requests.get(url)

        # print(response)
        response.raise_for_status()

        data = response.json()
        # print(json.dumps(data, indent=4))

        # data.items[0].contentDetails.relatedPlaylists.uploads
        # data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        channel_items = data["items"][0]
        channel_playlistId = channel_items["contentDetails"]["relatedPlaylists"]["uploads"]

        # print(channel_playlistId)
        return channel_playlistId
    
    except requests.exceptions.RequestException as e:
        raise e 


def get_video_ids(playlistId):

    video_ids = []
    pageToken = None

    base_url = f"https://youtube.googleapis.com/youtube/v3/playlistItems?part=contentDetails&&playlistId={playlistId}&maxResults={MAX_RESULTS}&key={API_KEY}"

    # they will be multiple pages, using "nextPageToken" and "prevPageToken" returned by the api call.

    try:
        while True:
            url = base_url

            if pageToken:
                url += f"&pageToken={pageToken}"

            response = requests.get(url)

            response.raise_for_status()
            
            data = response.json()
            for item in data.get('items', []):
                video_id = item['contentDetails']['videoId']
                video_ids.append(video_id)
            # END for

            pageToken = data.get('nextPageToken')

            if not pageToken:
                break

        # END while

        return video_ids

    except requests.exceptions.RequestException as e:
        raise e


def extract_video_data(video_ids):

    extracted_data = []

    def batch_list(video_id_list, batch_size):
        for video_id in range(0, len(video_id_list), batch_size):
            yield video_id_list[video_id: video_id + batch_size]
        # END for
    # END function

    try:
        for batch in batch_list(video_ids, MAX_RESULTS):
            video_ids_str = ",".join(batch)

            url = f"https://youtube.googleapis.com/youtube/v3/videos?part=contentDetails&part=snippet&part=statistics&id={video_ids_str}&key={API_KEY}"

            response = requests.get(url)

            response.raise_for_status()
            
            data = response.json()

            for item in data.get('items', []):
                video_id = item['id']
                snippet = item['snippet']
                contentDetails = item['contentDetails']
                statistics = item['statistics']
            
                videos_data = {
                    "video_id": video_id,
                    "title": snippet['title'],
                    "publishedAt": snippet['publishedAt'],
                    "duration": contentDetails['duration'],
                    "viewCount": statistics.get('viewCount', None),
                    "likeCount": statistics.get('likeCount', None),
                    "commentCount": statistics.get('commentCount', None),
                }

                extracted_data.append(videos_data)
            # END for item
        # END for batch

        return extracted_data

    except requests.exceptions.RequestException as e:
        raise e


if __name__ == "__main__":
    playlistId = get_playlist_id()
    print(playlistId)
    video_ids = get_video_ids(playlistId)
    print(extract_video_data(video_ids))
    