import os
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor

#%% static data
files = {'jobs':'Job Opportunities.xlsx'}

meta = {'requests':{'headers':{'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0'}}}

#%%
def random_url(df, co_name, exclude_list):
    url = df[(df['Company']==co_name) & (~df['URL'].isin(exclude_list))]['URL'].sample(1).tolist()[0]
    return(url)

#%% try 3 times max before exit
def check_url(co_name, link):
    attempt = 1
    while attempt<=3:

        # if status_code 400 (bad request), try without header
        status = requests.get(url=link, headers=meta['requests']['headers']).status_code
        if status==400:
            status = requests.get(url=link).status_code

        # try another random link if not successful
        if status!=200:
            link = random_url(dataframes['All'], co_name, [link])
            attempt = attempt + 1
        else:
            break

    if status!=200:
        print(f"[{co_name}, {status}]")

    return(status)

#%%
def pool_checkurl(list_links):
    status = {}
    with ThreadPoolExecutor(max_workers=min(os.cpu_count()*5, len(list_links))) as executor:
        for co_name,link in list_links.items():
            status[link] = executor.submit(check_url, co_name, link)
    status = {k:v.result() for k,v in status.items()}
    return(status)

#%% sample 1 job from each company and see if link is valid
dataframes = {'All':pd.read_excel(files['jobs'], sheet_name='All')}
dataframes['Sample'] = dataframes['All'].groupby(['Company']).sample(n=1)

#%%
dataframes['Status'] = pool_checkurl(dict(zip(dataframes['Sample']['Company'], dataframes['Sample']['URL'])))
dataframes['Status'] = pd.DataFrame(dataframes['Status'].items(), columns=['URL','Status'])
dataframes['Status']['Company'] = dataframes['Status']['URL'].map(dict(zip(dataframes['Sample']['URL'],
                                                                           dataframes['Sample']['Company'])))

dataframes['Status'].insert(0, 'Company', dataframes['Status'].pop('Company'))
dataframes['Status'] = dataframes['Status'].sort_values(by=['Status','Company'], ascending=(0,1))