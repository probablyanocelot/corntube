import urllib.request
import re
import os
import requests
from pytube import YouTube
from dotenv import load_dotenv
load_dotenv('.env')

YT_API_KEY = os.getenv('YT_API_KEY')

# # Download a youtube video
# def download_youtube_video(url):
#     yt = YouTube(url)
#     print(yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc())
#     # yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download(path)

# download_youtube_video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")



async def youtubeQuery(terms):
    ''' GET VIDEO BY BEST MATCH OF QUERY '''
    # print(terms)
    # terms = terms.split()
    # print(terms)
    print("line 26 " + term for term in terms)
    query = '+'.join(f"{term}" for term in terms)
    # print(query)
    html = urllib.request.urlopen(
        "https://www.youtube.com/results?search_query=" + query)
    # print("this is html"  + html)
    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    url = "https://www.youtube.com/watch?v=" + video_ids[0]
    title = getNameFromId(video_ids[0])
    # print(url)
    return url
# {
#         'title': title,
#         'url': url
#     }


def getNameFromId(id):
    url = requests.get(
        f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={id}&key={YT_API_KEY}').json()
    # url_json = json.loads(url)
    print(url)
    return
    title = url['items'][0]['snippet']['title']
    return title
    # title = url_json['entry']['title']['$t']
    # return title
    # author = json['entry']['author'][0]['name']


# HAVE TO USE API TO GET TITLE
def getVideoName(json_data):
    print(json_data)
    for item in json_data:

        print(json_data[item]['url'])
        # pattern = r"\??v?=?([^#\&\?]*).*/"
        pattern = '(?:youtube(?:-nocookie)?\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'

        if re.search(pattern, json_data[item]['url']):

            print(1)
            id = re.search(pattern, json_data[item]['url']).group(1)
            json_data[item]['title'] = getNameFromId(YT_API_KEY, id)

    print(json_data)
    return json_data



if __name__ == '__main__':
    print(YT_API_KEY)
    youtubeQuery('chloraseptic eminem')
    # json_data = {'0': {'title': 'asdfjldshkf',
    #                    'url': 'https://youtu.be/Hldov3JOopU'}}
    # get_vid_name(YT_API_KEY, json_data)
    # print(yt_query(YT_API_KEY, 'chloraseptic'))


# def try_title(id):
#     youtube = etree.HTML(urllib.request.urlopen(
#         f"http://www.youtube.com/watch?v={id}").read())
#     print(youtube)
#     video_title = youtube.xpath("//span[@id='eow-title']/@title")
#     print(video_title)


# def try_title(VideoID):

    # params = {"format": "json",
    #           "url": "https://www.youtube.com/watch?v=%s" % VideoID}
    # url = "https://www.youtube.com/oembed"
    # query_string = urllib.parse.urlencode(params)
    # url = url + "?" + query_string

    # with urllib.request.urlopen(url) as response:
    #     response_text = response.read()
    #     data = json.loads(response_text.decode())
    #     print(data['title'])
