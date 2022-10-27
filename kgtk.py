import os
import requests
import json
import pandas as pd


def call_semantic_similarity(input_file, url='https://kgtk.isi.edu/similarity_api'):
    file_name = os.path.basename(input_file)
    files = {
        'file': (file_name, open(input_file, mode='rb'), 'application/octet-stream')
    }
    resp = requests.post(url, files=files, params={'similarity_types': 'all'})
    if resp.status_code != 500:
        s = json.loads(resp.json())
        return pd.DataFrame(s)


def query_parent(qnode):
    url = 'https://query.wikidata.org/sparql'
    query = '''
    SELECT ?ancestor WHERE{
    wd:%s wdt:P31+|wdt:P279+ ?ancestor }

    ''' % (qnode)
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
        r = requests.get(url, params={'format': 'json', 'query': query}, headers=headers)

        data = r.json()
    except:
        print(r)
        return [c['ancestor']['value'].strip('http://www.wikidata.org/entity/') for c in data['results']['bindings']]





def map_qnode(query_items):
    url = 'https://query.wikidata.org/sparql'
    query = '''
    SELECT ?item ?prefLabel WHERE {
    VALUES ?prefLabel { "%s"@en }
    ?item rdfs:label ?prefLabel 
    
    }
''' % (query_items)
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
        r = requests.get(url, params={'format': 'json', 'query': query}, headers=headers)

        data = r.json()
    except:
        print(r)
