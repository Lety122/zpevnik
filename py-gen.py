import os
import re
import json

def generate_pwa_data(root_dir='.'):
    songs = []
    
    # TADY JE ZMĚNA: Nastavení základní cesty na serveru
    BASE_PATH = '/zpevnik/'
    
    # Základní soubory pro PWA se správnou cestou
    urls_to_cache = [
        f'{BASE_PATH}',
        f'{BASE_PATH}index.html',
        f'{BASE_PATH}manifest.json',
        f'{BASE_PATH}sw.js',
        f'{BASE_PATH}icon-192.png',
        f'{BASE_PATH}icon-512.png'
    ]
    
    title_pattern = re.compile(r'<title>(.*?)</title>', re.IGNORECASE | re.DOTALL)
    
    for dirpath, _, filenames in os.walk(root_dir):
        if 'index.html' in filenames:
            filepath = os.path.join(dirpath, 'index.html')
            rel_path = os.path.relpath(filepath, root_dir).replace('\\', '/')
            
            # Vynechání hlavního indexu v poli pro vyhledávání
            if rel_path == 'index.html':
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    match = title_pattern.search(content)
                    
                    if match:
                        title = match.group(1).strip()
                        # Do JS databáze (pro vyhledávač) stačí relativní cesta
                        songs.append({"title": title, "path": rel_path})
            except Exception as e:
                print(f"Chyba při čtení {filepath}: {e}")
            
            # ZMĚNA: Do SW cache vkládáme cestu i se složkou /zpevnik/
            urls_to_cache.append(f"{BASE_PATH}{rel_path}")

    songs.sort(key=lambda x: x['title'].lower())
    urls_to_cache.sort()

    js_songs = "const songs = [\n"
    for song in songs:
        js_songs += f"  {{ title: {json.dumps(song['title'], ensure_ascii=False)}, path: {json.dumps(song['path'])} }},\n"
    js_songs = js_songs.rstrip(',\n') + "\n];"

    js_cache = "const urlsToCache = [\n"
    for url in urls_to_cache:
        js_cache += f"  {json.dumps(url)},\n"
    js_cache = js_cache.rstrip(',\n') + "\n];"

    return js_songs, js_cache

if __name__ == '__main__':
    songs_output, cache_output = generate_pwa_data()
    print("VYHLEDÁVAČ do index.html:\n" + songs_output + "\n")
    print("CACHE do sw.js:\n" + cache_output)