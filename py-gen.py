import os
import re
import json

# Aktualizuje seznam písní v index.html, urlsToCache v sw.js
# a zvedne verzi cache (CACHE_NAME), aby si klienti stáhli nový obsah.
# Stačí přidat složku s písničkou a spustit: python3 py-gen.py

BASE_PATH = '/'
ROOT = os.path.dirname(os.path.abspath(__file__))


def collect_songs():
    songs = []
    title_pattern = re.compile(r'<title>(.*?)</title>', re.IGNORECASE | re.DOTALL)

    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        if 'index.html' not in filenames:
            continue
        filepath = os.path.join(dirpath, 'index.html')
        rel_path = os.path.relpath(filepath, ROOT).replace('\\', '/')
        if rel_path == 'index.html':
            continue

        with open(filepath, encoding='utf-8') as f:
            match = title_pattern.search(f.read())
        if not match:
            print(f'VAROVÁNÍ: {rel_path} nemá <title>, přeskakuji')
            continue
        songs.append({'title': match.group(1).strip(), 'path': rel_path})

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
    songs = collect_songs()
    update_index(songs)
    update_sw(songs)
