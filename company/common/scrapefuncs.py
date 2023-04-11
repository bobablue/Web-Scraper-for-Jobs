from common import errorhandling
import requests
import urllib.parse
import html
import json

#%% request
@errorhandling.requests_error
def pull(pulltype, json_decode=False, **kwargs):
    if pulltype=='get':
        response = requests.get(**kwargs)
    elif pulltype=='post':
        response = requests.post(**kwargs)
    if json_decode:
        return(response.json())
    return(response)

#%% add company name and date scraped to pulled data
def metadata(co, date):
    def add_meta(jobs_func):
        def wrapper(*args, **kwargs):
            func = jobs_func(*args)
            for i in func.values():
                i['Company'] = co
                i['Date Scraped'] = date
            return(func)
        return(wrapper)
    return(add_meta)

#%% include special characters in url instead of encoding (https://stackoverflow.com/a/12528097)
def encode(query, chars):
    l = []
    for k, v in query.items():
        k = urllib.parse.quote(str(k), safe=chars)
        v = urllib.parse.quote(str(v), safe=chars)
        l.append(k + '=' + v)
    return '&'.join(l)

#%% remove all encoding and multi-whitespaces from strings
def decode(str_obj):
    s = urllib.parse.unquote(str_obj)
    s = html.unescape(s)
    s = ' '.join(str(s.encode('ascii', errors='ignore'), 'utf-8').split())
    return(s)

#%% clean up location string
def clean_loc(data_dict):
    for i,j in data_dict.items():
        loc = ''.join(j['Location'].split())
        loc = loc.split(',')
        loc = set(i.lower() for i in loc)
        if loc=={'singapore'}:
            j['Location'] = 'Singapore'
    return(data_dict)

#%% save dict as json file
def to_json(co_name, jobs_dict):
    with open(f'{co_name}.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(jobs_dict, ensure_ascii=False, indent=4, sort_keys=True, default=str))