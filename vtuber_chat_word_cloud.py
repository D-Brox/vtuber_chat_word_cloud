import re
from os import path, rename, remove
from functools import partial
from pathlib import Path

__version__ = "0.0.13"

import asyncio
from tqdm.contrib.concurrent import process_map
from holodex.client import HolodexClient
from chat_downloader import ChatDownloader

import string
from matplotlib.font_manager import findSystemFonts
import numpy as np
from PIL import Image
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator

import typer

wc = typer.Typer(add_completion=False)

normal_word = r"(?:\w[\w']+)"
ascii_art = r"(?:[{punctuation}][{punctuation}]+)".format(punctuation=string.punctuation)
emoji = r"(?:[^\s])(?<![\w{ascii_printable}])".format(ascii_printable=string.printable)
regexp = r"{normal_word}|{ascii_art}|{emoji}".format(normal_word=normal_word, ascii_art=ascii_art, emoji=emoji)

font_paths = [f for f in findSystemFonts() if "NotoSansCJK-Light" in f]
font_path = font_paths[0] if len(font_paths) else None

def process_chat_log(vid_id):
    word_cloud_string = ""
    
    if not path.exists(f"backup/{vid_id}"):
        if path.exists(f"backup/{vid_id}.tmp"):
            remove(f"backup/{vid_id}.tmp")
        
        url = f"https://www.youtube.com/watch?v={vid_id}"
        chat = ChatDownloader().get_chat(url)       
        chat_log = open(f"backup/{vid_id}.tmp", 'w', encoding="utf-8", errors="ignore")
        for json_message in chat:                            
            text_msg = json_message['message']
            text_msg = re.sub(r':[a-zA-Z0-9_-]+:', '', text_msg)

            chat_log.write(text_msg + "\n")
            if(len(text_msg.strip()) > 0):
                word_cloud_string += text_msg + "\n"
        
        rename(f"backup/{vid_id}.tmp",f"backup/{vid_id}")
    else:
        chat_log = open(f"backup/{vid_id}", 'r', encoding='utf-8')
        for line in chat_log:
            word_cloud_string += line + '\n'
    
    return word_cloud_string

def generate_word_cloud(word_cloud_string,vid_id,name,mask,size,image_colors):
    width,height = size 
    width*=5
    height*=5
    wc = WordCloud(background_color='black',stopwords=STOPWORDS, collocations=True,
        max_font_size=512, min_font_size=8, max_words=6000, normalize_plurals= False,
        relative_scaling=0.5, mask=mask, random_state=3, min_word_length=2, repeat=True,
        width=width, height=height, scale=10, font_path=font_path)

    wc.generate(word_cloud_string)
    wc.recolor(color_func=image_colors)
    wc.to_file(f"output/{name}_{vid_id}.png")

async def get_video_ids(channel_id, api_key, max_videos=None):
    def is_public_stream(c):
        return c.status == "past" and c.topic_id not in ["membersonly", "shorts"]
    async with HolodexClient(key=api_key) as client:
        res = await client.get_videos_from_channel(channel_id, "videos", {"paginated":"true","limit":"0"})
        total = res["total"]
        if max_videos:
            total = min(max_videos,total)
        ids = []
        q = total // 25
        r = total % 25
        for i in range(q):
            videos = await client.videos_from_channel(channel_id, "videos", offset=i*25)
            ids += [c.id for c in videos.contents if is_public_stream(c)]
        if r:
            videos = await client.videos_from_channel(channel_id, "videos", limit = r, offset=q*25)
            ids += [c.id for c in videos.contents if is_public_stream(c)]

        return ids

async def get_channel_id(name,api_key):
    async with HolodexClient(key=api_key) as client:
        search = await client.autocomplete(name)
        contents = search.contents
        if len(contents) == 0:
            print(f"{name} not found")
            exit(1)
        content = contents[0]
        if content.type == "channel":
            print(f"Found channel: {content.text}")
            resp = input("Continue [Y/n] ").strip()
            if len(resp) == 0 or resp[0] in ("Y", "y"):
                return content.value

def process_and_generate(vid_id,name,mask,size,image_colors):
    try:
        word_cloud_string = process_chat_log(vid_id)
    except Exception as e:
        print(f"Could not get chat for URL, {vid_id}, skipping...")
        return

    if not path.exists(f"output/{name}_{vid_id}.png"):
        generate_word_cloud(word_cloud_string,vid_id,name,mask,size,image_colors)
    
    return word_cloud_string


@wc.command()
def channel(name:str = typer.Argument(...,help="Vtuber name"), image:Path= typer.Argument(...,help="Image for the word cloud"),api_key:str = typer.Argument(...,help="Holodex API key"), average:bool = typer.Argument(False,help="Average chat of all videos fetched"), max_videos:int = typer.Argument(None,help="Max number of videos fetched")):
    img = Image.open(image)
    size = img.size
    mask = np.array(img)
    image_colors = ImageColorGenerator(mask)

    channel_id = asyncio.run(get_channel_id(name,api_key))
    ids = asyncio.run(get_video_ids(channel_id,api_key,max_videos))

    process = partial(process_and_generate, name=name.split()[0], mask=mask, size=size, image_colors = image_colors)
    every_word_cloud = "".join(process_map(process, ids))   
    if average:
        generate_word_cloud(every_word_cloud,f"all_{max_videos}" if max_videos else "all", name, mask, size, image_colors)


def main():
    wc()

if __name__ == "__main__":
    main()