import json
import re
import requests
import argparse
from tqdm import tqdm

import os
os.environ['no_proxy'] = '*'


parser = argparse.ArgumentParser()
parser.add_argument("--playlist_id", type=str, default="426712570")
parser.add_argument("--cover_dir", type=str, default="covers")
parser.add_argument("--cache_dir", type=str, default="songs")
args = parser.parse_args()


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.115 Safari/537.36'
}
COOKIES = {"os": "pc"}

os.makedirs(args.cache_dir, exist_ok=True)
os.makedirs(args.cover_dir, exist_ok=True)


def get_play_list(playlist_id):
    url = f"http://music.163.com/playlist?id={playlist_id}" 
    contents = requests.get(url, headers=HEADERS, cookies=COOKIES).text

    playlist_name = re.search(r"<title>(.+)</title>", contents).group(1)[:-13]

    pattern = r'<li><a href="/song\?id=(\d+)">(.+?)</a></li>'
    song_list = re.findall(pattern, contents)

    return playlist_name, song_list


def get_song_info(song_id):
    url = f"http://music.163.com/song?id={song_id}"
    contents = requests.get(url, headers=HEADERS, cookies=COOKIES).text

    pattern = r'<meta property="og:music:artist" content="(.+?)".?/>'
    artist = re.search(pattern, contents).group(1)
    
    pattern = r'<meta property="og:image" content="(.+?)".?/>'
    cover_path = re.search(pattern, contents).group(1)

    pattern = r'<meta property="og:music:album" content="(.+?)".?/>'
    album_name = re.search(pattern, contents)
    if album_name is not None:
        album_name = album_name.group(1)
    else:
        album_name = "Unknown Album"

    return {
        "artist": artist,
        "cover_path": cover_path,
        "album_name": album_name,
    }


def load_song_info(song_id):
    out_file = os.path.join(args.cache_dir, f"{song_id}.json")
    if not os.path.exists(out_file):
        return None
    with open(out_file, "r", encoding="utf-8") as f:
        song_info = json.load(f)
    return song_info


def save_song_info(song_info):
    song_id = song_info["song_id"]
    out_file = os.path.join(args.cache_dir, f"{song_id}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(song_info, f, ensure_ascii=False, indent=4)


def get_all_song_info(song_list):
    song_infos = []
    print("Getting song infos...")
    for song_id, song_name in tqdm(song_list):
        song_info_cache = load_song_info(song_id)
        if song_info_cache is not None:
            song_infos.append(song_info_cache)
            continue
        try:
            song_info = get_song_info(song_id)
            song_info["song_id"] = song_id
            song_info["song_name"] = song_name
            save_song_info(song_info)
            song_infos.append(song_info)
        except Exception as e:
            print(f"Error on {song_id}")
    return song_infos


def download_covers(song_infos):
    print("Downloading covers...")
    album = set()
    covers = []
    for song_info in tqdm(song_infos):
        cover_path = song_info["cover_path"]
        cover_name = cover_path.split("/")[-1]
        album_name = song_info["album_name"]
        if album_name in album:
            continue

        album.add(album_name)
        covers.append(cover_name)

        save_path = os.path.join(args.cover_dir, cover_name)
        if os.path.exists(save_path):
            continue

        r = requests.get(cover_path)
        if r.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(r.content)

    with open("covers.json", "w", encoding="utf-8") as f:
        json.dump(covers, f, ensure_ascii=False, indent=4)


def main():
    playlist_name, song_list = get_play_list(args.playlist_id)
    # print(song_list)

    song_infos = get_all_song_info(song_list)
    download_covers(song_infos)


if __name__ == "__main__":
    main()