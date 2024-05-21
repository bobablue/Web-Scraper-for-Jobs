import os
import shutil
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import types

import company
from util import check_urls, g_sheets, scrape_funcs

#%% static data
folders = {'company':'company', 'archive':'archive'}
files = {'export':'Job Opportunities_{date}.xlsx', 'g_sheets_key':r'config/gsheets_key.json'}
cols = {'jobs':['Company', 'Title', 'URL', 'Location', 'Job Function', 'Date Scraped']}

#%% functions
#%% parallel requests
def pool_getjobs(list_scripts):
    jobs = {}
    with ThreadPoolExecutor(max_workers=min(os.cpu_count()*5, len(list_scripts))) as executor:
        for i in list_scripts:
            jobs[i] = executor.submit(list_scripts[i].get_jobs)

    for k in list(jobs):
        try:
            jobs[k] = jobs[k].result()
        except Exception as e:
            status['api_errors'].append((k,e))
            del jobs[k]

    return(jobs)

#%% latest timestamp from dataframe in file
def get_file_date(filepath):
    df = pd.read_excel(filepath, sheet_name='All')
    df['Date Scraped'] = pd.to_datetime(df['Date Scraped'])
    date = max(set(df['Date Scraped']))
    return(date.strftime('%Y-%m-%d %H%M'))

#%% get list of company scripts
scripts = {k:v for k,v in company.__dict__.items() if isinstance(v, types.ModuleType) and v.__name__.startswith('company')}

#%% run through all company scripts to get jobs data
status = {'api_errors':[]}
jobs = {'dict':pool_getjobs(scripts)}

#%% parse jobs dict to dataframe
jobs['dataframe'] = pd.DataFrame.from_dict({v1:jobs['dict'][k1][v1] for k1 in jobs['dict'].keys() for v1 in jobs['dict'][k1].keys()},
                                           orient='index')

jobs['dataframe'] = jobs['dataframe'].reset_index().rename(columns={'index':'URL'})

# some companies are split into multiple sources. combine all to same company name by splitting out separator.
jobs['dataframe']['Company'] = jobs['dataframe']['Company'].str.split('_').str[0]
jobs['dataframe'] = jobs['dataframe'][cols['jobs']].sort_values(by=['Company','Location','Title'], key=lambda x:x.str.lower())
jobs['dataframe'] = jobs['dataframe'].reset_index(drop=True)

print(f"{len(jobs['dataframe'])} job opportunities from {len(set(jobs['dataframe']['Company']))} companies")

#%% sample check if job URLs are valid. if status is 404, API has probably changed, so code needs an update.
status['sample'] = check_urls.run_checks(jobs['dataframe'])
status['sample_errors'] = status['sample'][status['sample']['Status']!=200]
status['sample_errors'] = dict(zip(status['sample_errors']['Company'], status['sample_errors']['Status']))

#%%
if status['api_errors']:
    print('API errors', *sorted(status['api_errors'], key=lambda x:x[0].lower()), sep='\n')

if status['sample_errors']:
    print('URL errors:', status['sample_errors'])

#%% if no API errors, archive current file and save latest output
if not status['api_errors'] and os.path.isfile(i:=files['export'].replace('_{date}','')):
    shutil.move(i, os.path.join(folders['archive'], files['export'].replace('{date}', get_file_date(i))))
    scrape_funcs.save_xlsx({'All':jobs['dataframe']}, files['export'].replace('_{date}', ''))

#%% export to google sheets (doesn't matter if errors exist)
g_sheets.auth(files['g_sheets_key'])
g_sheets.update(df=jobs['dataframe'], g_sheet_key='1NuJjghe752QkHOe92w3OtQs6wfO0e74l_HQxZkW9YSs')