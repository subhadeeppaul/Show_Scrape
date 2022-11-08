import json
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

def get_from_file(id: int, data):
    return_data = {'url': f'https://apis.justwatch.com/content/titles/show/{id}/locale/en_IN?language=en'}
    
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
        # download_image(data['id'], return_data['poster'])
    if 'seasons' in return_data:
        for season in return_data['seasons']:
            if 'poster' in season:
                season['poster'] = season['poster'].replace('{profile}', f's276/{name}.webp')
    return return_data

if __name__ == '__main__':
    n = int(input('Enter limit: '))
    load_genres()
    load_providers()
    
    data = json.load(open('data1.json'))
    arr = []
    for i in range(n):
        arr.append(get_from_file(i + 1, data[i]))
        print(f'Processed {i + 1}/{n}')

    json.dump(arr, open('result2.json', 'w'), indent=2)
