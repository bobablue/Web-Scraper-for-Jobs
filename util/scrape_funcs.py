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
def num_jobs(script_name):
    def inner(func):
        def wrapper(*args, **kwargs):
            module_name = os.path.splitext(os.path.basename(script_name))[0]
            output = func(*args, **kwargs)
            print(f"[{module_name}, {len(output)}]")
            return(output)
        return(wrapper)
    return(inner)

#%% request
@error_handling.requests_error
def pull(pulltype, json_decode=False, **kwargs):
    timeout = 30
    if pulltype=='get':
        response = requests.get(timeout=timeout, **kwargs)
    elif pulltype=='post':
        response = requests.post(timeout=timeout, **kwargs)
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
        loc = j['Location'].replace('-',',')
        loc = ''.join(loc.split())
        loc = loc.split(',')
        loc = set(i.lower() for i in loc if not i.isdigit()) # remove postal codes if present
        if loc.issubset({'sg','singapore','centralsingapore'}):
            j['Location'] = 'Singapore'
    return(data_dict)

#%% restrict to selected locations only
def restrict_loc(data_dict, loc_list):
    restricted = {k:v for k,v in data_dict.items() if any(x in v['Location'].lower() for x in loc_list)}
    return(restricted)

#%% save dict as json file
def to_json(co_name, jobs_dict):
    with open(f'{co_name}.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(jobs_dict, ensure_ascii=False, indent=4, sort_keys=True, default=str))

#%% save a list of dataframes into a single excel workbook
def save_xlsx(list_dfs, filename):
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        for ws,df in list_dfs.items():
            index = df.index.nlevels if df.index.nlevels>1 else 0
            df.to_excel(writer, sheet_name=ws, index=False, freeze_panes=(1,0))
            writer.sheets[ws].autofilter(*[df.columns.nlevels-1, 0, df.columns.nlevels-1, index+len(df.columns)-1])