import os
import re
import glob
import json
import chordpro

# Vyrenderuje každou píseň ze song.pro do index.html, aktualizuje seznam písní
# v index.html a urlsToCache v sw.js a zvedne verzi cache (CACHE_NAME).
# Přidání/úprava písně: edituj song.pro a spusť: python3 py-gen.py

BASE_PATH = '/'
ROOT = os.path.dirname(os.path.abspath(__file__))


def song_pros():
    return sorted(glob.glob(os.path.join(ROOT, '[0-9][0-9][0-9][0-9]', '*', 'song.pro')))


def render_all_songs():
    n = 0
    for pro in song_pros():
        doc = chordpro.parse_pro(open(pro, encoding='utf-8').read())
        out = os.path.join(os.path.dirname(pro), 'index.html')
        with open(out, 'w', encoding='utf-8') as f:
            f.write(chordpro.render_page(doc))
        n += 1
    print(f'rendered {n} songs')


def collect_songs():
    songs = []
    for pro in song_pros():
        doc = chordpro.parse_pro(open(pro, encoding='utf-8').read())
        rel = os.path.relpath(os.path.join(os.path.dirname(pro), 'index.html'), ROOT).replace('\\', '/')
        if not doc['title']:
            print(f'VAROVÁNÍ: {rel} nemá {{title}}, přeskakuji')
            continue
        songs.append({'title': doc['title'], 'path': rel})
    songs.sort(key=lambda s: s['title'].lower())
    return songs


def replace_block(text, start_marker, end_marker, replacement):
    start = text.index(start_marker)
    end = text.index(end_marker, start) + len(end_marker)
    return text[:start] + replacement + text[end:]


def update_index(songs):
    path = os.path.join(ROOT, 'index.html')
    with open(path, encoding='utf-8') as f:
        html = f.read()

    lines = [f'  {{ title: {json.dumps(s["title"], ensure_ascii=False)}, '
             f'path: {json.dumps(s["path"])} }},' for s in songs]
    block = 'const songs = [\n' + '\n'.join(lines).rstrip(',') + '\n];'
    html = replace_block(html, 'const songs = [', '];', block)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'index.html: {len(songs)} písní')


def update_sw(songs):
    path = os.path.join(ROOT, 'sw.js')
    with open(path, encoding='utf-8') as f:
        sw = f.read()

    urls = [BASE_PATH, f'{BASE_PATH}index.html', f'{BASE_PATH}manifest.json',
            f'{BASE_PATH}sw.js', f'{BASE_PATH}icon-192.png', f'{BASE_PATH}icon-512.png']
    urls += [f'{BASE_PATH}{s["path"]}' for s in songs]
    urls.sort()

    lines = [f'  {json.dumps(u)},' for u in urls]
    block = 'const urlsToCache = [\n' + '\n'.join(lines).rstrip(',') + '\n];'
    sw = replace_block(sw, 'const urlsToCache = [', '];', block)

    version_pattern = re.compile(r'(zpevnik-cache-v)(\d+)')
    old_version = int(version_pattern.search(sw).group(2))
    sw = version_pattern.sub(f'\\g<1>{old_version + 1}', sw)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(sw)
    print(f'sw.js: {len(urls)} souborů v cache, verze v{old_version} -> v{old_version + 1}')


if __name__ == '__main__':
    render_all_songs()
    songs = collect_songs()
    update_index(songs)
    update_sw(songs)
