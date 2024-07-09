from bs4 import BeautifulSoup
import json
import os
import shutil
import argparse
import random

song_template = '''
<a href="{pic_path}">
    <img alt="{album_name}" src="{pic_path}"/>
</a>
'''

group_template = '''
<div class="scroll img-box" style="--t: {t}s">
    <div>
    {sub_group1}
    </div>

    <div>
    {sub_group2}
    </div>
</div>
'''


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", type=str, default="html")
    parser.add_argument("--template_dir", type=str, default="html_template")
    parser.add_argument("--cover_dir", type=str, default="covers")
    parser.add_argument("--cover_list", type=str, default=None)
    parser.add_argument("--max_num_albums",type=int,default=400)
    parser.add_argument("--num_rows",type=int,default=5)

    args = parser.parse_args()

    output_dir = args.output_dir
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    shutil.copytree(args.template_dir, args.output_dir)

    target_cover_dir = os.path.join(args.output_dir,'covers')
    os.makedirs(target_cover_dir,exist_ok=True)

    if args.cover_list is None:
        cover_list = os.listdir(args.cover_dir)
    else:
        with open(args.cover_list, 'r',encoding='utf-8') as f:
            cover_list = json.load(f)
    if len(cover_list) > args.max_num_albums:
        cover_list = cover_list[:args.max_num_albums]
    albums = []
    
    for pic_name in cover_list:
        pic_path = f'covers/{pic_name}'
        source_pic_path = os.path.join(args.cover_dir, pic_name)
        target_pic_path = os.path.join(args.output_dir,"covers",pic_name)
        shutil.copy(source_pic_path,target_pic_path)
        song_html = song_template.format(pic_path=pic_path, album_name='unknown')
        albums.append(song_html)
        
    num_rows = args.num_rows
    group_size = len(albums) // num_rows
    max_num_albums = group_size * num_rows
    albums = albums[:max_num_albums]

    random.shuffle(albums)

    html_template_path = os.path.join(args.template_dir, 'index.html')
    with open(html_template_path, 'r',encoding='utf-8') as f:
        html_template = f.read()
    template_soup = BeautifulSoup(html_template, 'html.parser')
    # find body
    container = template_soup.find('body') 
    # remove all children
    container.clear()

    for i in range(0, len(albums), group_size):
        sub_group1 = ''.join(albums[i:i+group_size//2])
        sub_group2 = ''.join(albums[i+group_size//2:i+group_size])
        t = random.randint(50,60) * group_size * 8 / 40
        t = int(t)
        group_html = group_template.format(sub_group1=sub_group1, sub_group2=sub_group2, t=t)
        container.append(BeautifulSoup(group_html, 'html.parser'))


    output_path = os.path.join(output_dir, 'index.html')
    with open(output_path, 'w',encoding='utf-8') as f:
        f.write(str(template_soup))



