import json
import os
import re
import requests


COLUMNS = ['title', 'poster', 'poster_blur_hash', 'id','short_description', 'original_release_year',  'seasons']

client = requests.session()
genres = {}
providers = {}
poster_folder = 'posters'

def load_genres():
    '''Load genres from justwatch'''
    res = client.get('https://apis.justwatch.com/content/genres/locale/en_IN')
    data = res.json()
    for genre in data:
        # Store genre id and name in dictionary
        genres[int(genre['id'])] = genre['technical_name']

def load_providers():
    '''Load providers from justwatch'''
    res = client.get('https://apis.justwatch.com/content/providers/locale/en_IN')
    data = res.json()
    for provider in data:
        providers[int(provider['id'])] = provider['technical_name']

def download_image(file_id: str, image_url: str):
    base = 'https://images.justwatch.com'
    res = client.get(base + image_url, stream=True)
    if (res.status_code == 200):
        ext = image_url.split('.')[-1]
        if not os.path.exists(poster_folder):
            os.mkdir(poster_folder)
        with open(f'{poster_folder}/{file_id}.{ext}', 'wb') as file:
            for chunk in res.iter_content(1021):
                file.write(chunk)

def get_data(id: int):
    show_url = f'https://apis.justwatch.com/content/titles/show/{id}/locale/en_IN?language=en'

    response = client.get(show_url)
    data = response.json() # convert to dictionary
    return_data = {'url': show_url}
    
    if response.status_code != 200:
        print(f'{id} failed')
        return_data.update({'error': response.status_code})
        return return_data

    # Get name slug from title
    name = None
    if 'full_path' in data:
        name = data['full_path'].split('/')[-1]

    if not name and 'title' in data:
        sanitized = re.sub(r'[^\w\s]', '', data['title'])
        name = sanitized.replace(' ', '-').lower()

    if not name and 'original_title' in data:
        sanitized = re.sub(r'[^\w\s]', '', data['original_title'])
        name = sanitized.replace(' ', '-').lower()
    
    if not name: name = '{profile}'  # Fallback name

    # Get Platforms
    return_data['available_platforms'] = set()
    if 'offers' in data:
        for offer in data['offers']:
            if offer['provider_id'] not in providers:
                continue
            provider = providers[offer['provider_id']]
            return_data['available_platforms'].add(provider)
    return_data['available_platforms'] = list(return_data['available_platforms'])

    # Find IMDB Score
    if 'scoring' in data:
        for score in data['scoring']:
            if score['provider_type'] == 'imdb:score':
                return_data['IMDB_rating'] = score['value']

    # Required columns
    for c in COLUMNS:
        if c in data:
            return_data[c] = data[c]

    # Genres
    if 'genre_ids' in data:
        return_data['genres'] = [genres[genre_id] for genre_id in data['genre_ids']]  

    # Replace {profile} with slug
    if 'poster' in return_data:
        return_data['poster'] = return_data['poster'].replace('{profile}', f's276/{name}.webp')
        download_image(data['id'], return_data['poster'])
    if 'seasons' in return_data:
        for season in return_data['seasons']:
            if 'poster' in season:
                season['poster'] = season['poster'].replace('{profile}', f's276/{name}.webp')
    return return_data

if __name__ == '__main__':
    n = int(input('Enter limit: '))
    load_genres()
    load_providers()
    arr = []
    for i in range(n):
        arr.append(get_data(i + 1))
        print(f'Processed {i + 1}/{n}')

    json.dump(arr, open('result1.json', 'w'), indent=2)
