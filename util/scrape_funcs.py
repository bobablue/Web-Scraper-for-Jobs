from util import error_handling
import os
import pandas as pd
import requests
import urllib.parse
import html
import json

#%%
def get_urls(filepath, company_name):
    urls = pd.read_csv(filepath)
    urls = urls[urls['company']==company_name]
    urls = urls.to_dict(orient='records')[0] # should only have 1 record per company
    urls = {k:v for k,v in urls.items() if v==v} # remove nan values
    return(urls)

#%%
def track_status(script_name):
    def inner(func):
        def wrapper(*args, **kwargs):
            module_name = os.path.splitext(os.path.basename(script_name))[0]
            output = func(*args, **kwargs)
            print(f"[{module_name}] {len(output)}")
            return(output)
        return(wrapper)
    return(inner)

#%% request
@error_handling.requests_error
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

#%% update total number of jobs in various parameter objects
def update_num_jobs(num_jobs, finder, url):
    finder['limit'] = num_jobs
    url['finder'] = f"findReqs;{','.join(f'{k}={v}' for k,v in finder.items())}"
    return(finder, url)

#%% include special characters in url instead of encoding (https://stackoverflow.com/a/12528097)
def encode(query, chars):
    encoded = []
    for k, v in query.items():
        k = urllib.parse.quote(str(k), safe=chars)
        v = urllib.parse.quote(str(v), safe=chars)
        encoded.append(k + '=' + v)
    return '&'.join(encoded)

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