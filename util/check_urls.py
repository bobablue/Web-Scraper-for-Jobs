import os
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor

#%% static data
files = {'jobs':os.path.join(os.path.dirname(os.getcwd()), 'Job Opportunities.xlsx')}

meta = {'requests':{'headers':{'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0'},
                    'timeout':10},

        'company':{'Revolut':{'Accept-Language':'en-US,en;q=0.5',
                              'Priority':'u=0, i'}}}

#%%
def random_url(df, co_name, exclude_list):
    url = df[(df['Company']==co_name) & (~df['URL'].isin(exclude_list))]['URL'].sample(1).tolist()[0]
    return(url)

#%% try 3 times max before exit
def check_url(jobs_df, co_name, link):

    # some companies have specific headers
    headers = meta['requests']['headers']
    if co_name in meta['company']:
        headers = headers | meta['company'][co_name]

    attempt = 1
    while attempt<=3:

        # if status_code 400 (bad request), try without header
        try:
            status = requests.get(url=link, headers=headers, timeout=meta['requests']['timeout']).status_code

        except requests.exceptions.Timeout:
            continue

        if status in [400]:
            status = requests.get(url=link, timeout=meta['requests']['timeout']).status_code

        # try another random link if not successful
        if status!=200:
            link = random_url(jobs_df, co_name, [link])
            attempt = attempt + 1
        else:
            break

    return(status)

#%%
def pool_checkurl(jobs_df, list_links):
    status = {}
    with ThreadPoolExecutor(max_workers=min(os.cpu_count()*5, len(list_links))) as executor:
        for co_name,link in list_links.items():
            status[link] = executor.submit(check_url, jobs_df, co_name, link)
    status = {k:v.result() for k,v in status.items()}
    return(status)

#%%
def run_checks(jobs_df):
    sample_df = jobs_df.groupby(['Company']).sample(n=1)

    status_df = pool_checkurl(jobs_df, dict(zip(sample_df['Company'], sample_df['URL'])))
    status_df = pd.DataFrame(status_df.items(), columns=['URL','Status'])
    status_df['Company'] = status_df['URL'].map(dict(zip(sample_df['URL'], sample_df['Company'])))
    status_df.insert(0, 'Company', status_df.pop('Company'))
    status_df = status_df.sort_values(by=['Status','Company'], ascending=(0,1))
    return(status_df)

#%% sample job(s) from each company and see if link is valid. if status is 404, API has probably changed.
if __name__=='__main__':
    dataframes = {'all':pd.read_excel(files['jobs'], sheet_name='All')}

    dataframes['status'] = run_checks(dataframes['all'])

    dataframes['errors'] = dataframes['status'][dataframes['status']['Status']!=200]
    dataframes['errors'] = dict(zip(dataframes['errors']['Company'], dataframes['errors']['Status']))

    if dataframes['errors']:
        print('URL errors:', dataframes['errors'])