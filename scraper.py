import requests
import time 
import csv
import json
import sys

import os
import googleapiclient.discovery

""" scrape youtube channel to build table of contents html file and 
    csv of video information for excel file
    note this code has a slow down delay to meet youtube terms of use
"""

# Google Cloud API Key AIzaSyDwfhQg2edBjo1PUw0-poIbKYBQ4mEigRI
api_key = 'AIzaSyDwfhQg2edBjo1PUw0-poIbKYBQ4mEigRI'

homeo_channel_url = 'https://www.youtube.com/channel/UCi77mTy9Il5eOFUUvgoxICA' + "/videos"
larger_homeo_url = 'https://www.youtube.com/channel/UCagzdMtT3xLjh2MpZX2L44w' + "/videos"

api_service_name = "youtube"
api_version = "v3"
DEVELOPER_KEY = api_key

max_result = 50
loop_counter = 0

youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey = DEVELOPER_KEY)

def main():

        # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    
    #Generate Fresh Channel List.
    # spreadsheet_to_json()
    t1 = "UCGW2Yqy7GvjDg92HdW9urdA"
    t2 = "madinmikala"
    print(get_channel_details(t2))

    # Create a dict object from the json channel list
    # with open('data/channel-list.json') as json_file:
    #     channel_data = json.load(json_file)
    #     channel_list = []
    #     for i in channel_data.keys():
    #         if channel_data[i]["video_list"] == False:
    #             channel_list.append(i)
    # json_file.close()

    # parse_channel_list(channel_list)
    
    

def spreadsheet_to_json():
    """ Take a spreadsheet pulls out channel and user links ids. Add them and their catagory to the channel-list json file 
    JSON file includes: channel name, channel i
    d, channel catagory, video list completed, video view count completed."""
    count = 0
    channels = {}

    with open("data/Research Project Plan and Data List - Channel List.csv","r") as csv:
        for i in csv:
            count += 1
            i = i.split(",")
            channel_title = i[0]
            link = i[1]
            link = link.split("/")

            if link[3] == 'channel' or link[3] == 'user':
                id = link[4]
                if link[3] == 'channel':
                    channel_type = "channel"
                else:
                    channel_type = "user"
            else:
                id = link[3]
            
            channels[id] = { "channel_title": channel_title, "channel_type": channel_type, "video_list": False, "video_views": False}

    csv.close()


    if os.stat("data/channel-list.json").st_size == 0:

        open("data/channel-list.json", 'w').close()

        with open("data/channel-list.json", 'w') as l:
            # Add a check so it doesn't erase
            json.dump(channels, l, indent=4)    
    else:
        inp = ""

        while(True):
            inp = input("Do you want to overwrite the channel_list this will wipe any booleayn processes?")

            if inp == "yes" or inp == "no":
                break


        while(True):
            inp2 = input("Are you sure?")
            if inp2 == "yes" or inp2 == "no":
                break
            
            

        if inp == "yes" and inp2 == "yes":
            open("data/channel-list.json", 'w').close()

            with open("data/channel-list.json", 'w') as l:
                # Add a check so it doesn't erase
                json.dump(channels, l, indent=4)
        
        l.close()

    # parse_channel_list([test_id])

    return None # Returns list of ids.


def parse_channel_list(channel_list):
    """ parses a entire channel list for video stat extraction """

    # Create Checklist of Channels not Audited Incase Quota runs out or other reasons
    channel_parse_list = []

     # Mark channel as done in file.
    with open('data/channel-list.json', 'r') as json_file:
        channel_file = json.load(json_file)
        for i in channel_file:
            if channel_file[i]["video_list"] == False:
                channel_parse_list.append(i)

    print(channel_parse_list)

    for channelId in channel_parse_list:

        # Get Channel ID/Uploads Playlist ID
        # Dictionary Format
        # {channel_title, channel_description, upload_playlist_id, channel_country, channel_start_pub, channel_view_count, channel_commentCount, channel_subscriber_count}        
        channel_data = get_channel_details(channelId)

        # Pull all video data from channel checking for multiple page retrievals.
        video_data = playlist_videos(channel_data['upload_playlist_id'], None)

        # Set the amount of pages processed
        channel_data["channel_upload_total_pages"] = loop_counter

        # Add video data under the key video data
        channel_data['video_data'] = video_data

        # Clear File if already populated
        open("data/channel_videos/"+ channel_data["channel_id"] , 'w').close()

        # Write Video Data to JSON File
        with open("data/channel_videos/"+ channel_data["channel_id"], 'w') as f:
            json.dump(channel_data, f, indent=4)
        
        # Mark channel as done in file.
        with open('data/channel-list.json', 'r') as json_file:
            channel_file = json.load(json_file)
            for i in channel_file:
                # print(i)
                if i == channelId:
                    print(channel_file[i])
                    channel_file[i]["video_list"] = True
            
        with open('data/channel-list.json', 'w') as json_file:
            json.dump(channel_file, json_file, indent=4)
        print("Channel ID: " + channelId + " Done.")



def user_channel_id(channelName):

    user_channel_data = youtube.channels().list(part="id", forUsername=channelName).execute()
    user_channel_id = user_channel_data['items'][0]['id']
    return user_channel_id

# Get the ID of the uploads playlist for a Channel
def get_channel_details(channelId):
    """ Finds the uploads playlist for a channel for a channel using the youtube data API """

    channel_list = youtube.channels().list(
        part = "snippet,contentDetails, statistics",
        id = channelId
    ).execute()

    items = channel_list['items'][0] # fetch the dictionary in the items list.

    channel_details = {
        'channel_title': items['snippet']['title'],
        'channel_description': items['snippet']['description'],
        'upload_playlist_id': items['contentDetails']['relatedPlaylists']['uploads'],
        'channel_id': items['id'],
        'channel_start_pub': items['snippet']['publishedAt'],
        'channel_view_count': items['statistics']['viewCount'],
        'channel_commentCount': items['statistics']['commentCount'],
        'channel_subscriber_count': items['statistics']['subscriberCount'],
        'channel_video_count': items['statistics']['videoCount'],
        'channel_country': items['snippet']['country']
    }

    return channel_details

# Fetch all the videos from a playlist id, option next page token for multi-page retrievals.
def playlist_videos(id, next_page_token):

    global  loop_counter
    loop_counter += 1

    # Null check for next page tokens.
    if next_page_token == None:
        print("Debug Path: If")
        pageVideos = youtube.playlistItems().list(
            part = "contentDetails, snippet",
            playlistId = id,
            maxResults = max_result
        ).execute()

    else:
        pageVideos = youtube.playlistItems().list(
            part = "contentDetails, snippet",
            playlistId = id,
            maxResults = max_result,
            pageToken = next_page_token # If the next page token exists get the next page results.
        ).execute()

    video_details = {}

    # Check if theres a next page token in the video data is so add it to the dictionary to be returned.
    if 'nextPageToken' in pageVideos.keys():
        next_page_token = pageVideos['nextPageToken']
    else:
        print("Last Page Reached: Page " + str(loop_counter))
        next_page_token = None
        


    #  Extract all videos from the uploaded playlist of a channel. If theres a next token add it to the channel details.
    videos_list = pageVideos.get('items', [])


    for video in videos_list:
        videoId = video['contentDetails']['videoId']
        videoTitle = video['snippet']['title']
        channelId= video['snippet']['channelId']
        videoPubDate = video['contentDetails']['videoPublishedAt']

        video_details[videoId] = {'video_title': videoTitle, "channel_id": channelId, "pub_date": videoPubDate, "views": 0}

    # If page token exists then recursively fetch each page and join into a single dictionary.


    if next_page_token != None:
        video_details = {**video_details, **playlist_videos(id, next_page_token)}

    
    return video_details

def video_view_extraction:

    # check video_boolean completion


    #Video File Loop


    # Mark Completed


    




if __name__ == "__main__":
    main()