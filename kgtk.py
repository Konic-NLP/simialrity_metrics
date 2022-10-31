import os
import requests
import json
import pandas as pd


def call_semantic_similarity(input_file, url='https://kgtk.isi.edu/similarity_api'):
    '''



    :param input_file:  a tsv files, two columns and each row is pair of qnodes
    :param url: kgtk api url
    :return: a tsv file including six types of similarity score from kgtk for each row in the input_file
    '''
    file_name = os.path.basename(input_file)
    files = {
        'file': (file_name, open(input_file, mode='rb'), 'application/octet-stream')
    }
    resp = requests.post(url, files=files, params={'similarity_types': 'all'})
    if resp.status_code != 500:
        s = json.loads(resp.json())
        return pd.DataFrame(s)


def query_parent(qnode):
    '''
     input a qnode, and return all the ancestors with which the input qnode has a instance-of /subcloss of, this functon
     is used for filtering the re-mapped qnode
    :param qnode:
    :return: all ancestors qnode
    '''
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
    '''

    mapped based on the argument value and return all the qnodes which entry is the query items
    :param query_items:
    :return:qnode
    '''
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
        return data
    except:
        print(r)

