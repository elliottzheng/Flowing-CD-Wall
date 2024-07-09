from selenium import webdriver
import time
import os
from bs4 import BeautifulSoup
import requests
from tqdm import tqdm
import argparse
import json
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

def get_song_ids(driver, playlist_id):
    playlist_url = f"https://y.qq.com/musicmac/v6/playlist/detail.html?id={playlist_id}"
    print(playlist_url)
    driver.get(playlist_url)
    # driver.implicitly_wait(10)
    start = time.time()
    timeout = 100
    while True:
        if time.time() - start > timeout:
            raise TimeoutError
        if len(driver.find_elements(By.CLASS_NAME, "songlist__item")) > 0:
            break
        time.sleep(1)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    songs = []
    for song in soup.find_all(class_="songlist__item"):
        song_mid = song["mid"]
        url = f"https://y.qq.com/n/ryqq/songDetail/{song_mid}"
        singers = song.find_all(class_="singer_name")
        # for singer in singers:
        #     print(singer['title'])
        song_name = song.find(class_="mod_songname__name")["title"]
        song_info = {
            "song_mid": song_mid,
            "song_name": song_name,
            "singers": [singer["title"] for singer in singers],
            "url": url,
        }
        songs.append(song_info)
    return songs


def assert_login(driver):
    while True:
        try:
            driver.find_element(By.CLASS_NAME, "yqq-dialog-content")
            print("Please login")
            time.sleep(3)
        except NoSuchElementException:
            break

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--playlist_id", type=str, default="8081238754")
    parser.add_argument("--cover_dir", type=str, default="covers")

    args = parser.parse_args()

    playlist_id = args.playlist_id

    cover_dir = args.cover_dir
    os.makedirs(cover_dir, exist_ok=True)

    chrome_options = webdriver.ChromeOptions()
    cwd = os.getcwd()
    abs_cwd = os.path.abspath(cwd).replace("\\", "/")
    chrome_options.add_argument(f"--user-data-dir={abs_cwd}/chrome_data")
    # chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=chrome_options)

    songs = get_song_ids(driver, playlist_id)
    max_num_songs = 500
    song_infos = []

    song_dir = "songs"
    os.makedirs(song_dir, exist_ok=True)

    login_confirm = False

    for i, song in enumerate(tqdm(songs[:max_num_songs])):
        song_mid = song["song_mid"]
        url = song["url"]
        out_file = f"songs/{song_mid}.json"
        if os.path.exists(out_file):
            with open(out_file, "r", encoding="utf-8") as f:
                song_info = json.load(f)
            song_infos.append(song_info)
            continue

        driver.get(url)
        driver.implicitly_wait(10)

        if not login_confirm:
            assert_login(driver)
            login_confirm = True

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        # data_info__item_song
        infos = soup.find_all(class_="data_info__item_song")
        song_info = {}
        song_info.update(song)
        try:
            album_url = infos[0].find("a").get("href")
            # print(infos[0].text.replace('专辑：',''))
            album_name = infos[0].text.replace("专辑：", "")

            assert "albumDetail" in album_url
            song_info["album_name"] = album_name
            song_info["album_url"] = album_url

        except:
            pass

        scripts = soup.find_all("script")
        list_names = []
        picurl = None
        for script in scripts:
            text = str(script)
            if not text.startswith("<script>window"):
                continue
            text = text.replace("<script>", "").replace("</script>", "")
            segs = text.split("; ")
            for seg in segs:
                if seg.startswith("window.__INITIAL_DATA__"):
                    seg = seg.split('"picurl":"')[1]
                    seg = seg.split('",')[0]
                    # print(seg)
                    picurl = seg
                    # \u002F -> /
                    picurl = picurl.replace("\\u002F", "/")
                    picurl = "https:" + picurl

                    # 300->800
                    picurl = picurl.replace("300x300", "800x800")
                    # print(picurl)
        if picurl is None:
            # continue
            raise
        song_info["picurl"] = picurl

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(song_info, f, ensure_ascii=False, indent=4)

        song_infos.append(song_info)

    with open("song_infos.json", "w", encoding="utf-8") as f:
        json.dump(song_infos, f, ensure_ascii=False, indent=4)

    print('downloading images')
    albums = set()
    covers = []
    for song_info in tqdm(song_infos):
        pic_url = song_info['picurl']
        pic_name = pic_url.split('/')[-1].replace('?max_age=2592000', '')
        pic_path = os.path.join(cover_dir, pic_name)
        album_name = song_info.get('album_name', 'Unknown')
        if album_name in albums:
            continue
        albums.add(album_name)
        covers.append(pic_name)
        if os.path.exists(pic_path):
            continue
        r = requests.get(pic_url)
        if r.status_code == 200:
            with open(pic_path, 'wb') as f:
                f.write(r.content)
            
    print('done')
    with open("covers.json", "w", encoding="utf-8") as f:
        json.dump(covers, f, ensure_ascii=False, indent=4)