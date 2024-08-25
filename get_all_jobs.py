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

#%%
def retry_getjobs(list_scripts):
    status['api_errors'] = [] # clear api_errors status list before retrying
    jobs_dict = pool_getjobs(list_scripts)
    return(jobs_dict)

#%% latest timestamp from dataframe in file
def get_file_date(filepath):
    df = pd.read_excel(filepath, sheet_name='Summary')
    df['Date Scraped'] = pd.to_datetime(df['Date Scraped'])
    date = max(set(df['Date Scraped']))
    return(date.strftime('%Y-%m-%d %H%M'))

#%% summary of number of jobs for each company
def summarize(df):
    date_scraped = sorted(list(set(df['Date Scraped'])))[0]

    s_df = df.copy()
    s_df = s_df.groupby(['Company'], as_index=False)['URL'].count()

    # include companies with 0 jobs
    companies_zero = set([i.split('_')[0] for i in scripts]) - set(s_df['Company'])
    print(f"No postings from: {sorted(list(companies_zero))}")
    companies_zero = pd.DataFrame(companies_zero, columns=['Company'])
    companies_zero['URL'] = 0

    s_df = pd.concat([s_df, companies_zero], ignore_index=True)
    s_df['Date Scraped'] = date_scraped
    s_df = s_df.rename(columns={'URL':'Number of Job Postings'})
    s_df = s_df.sort_values(by=['Company'], key=lambda x:x.str.lower()).reset_index(drop=True)
    return(s_df)

#%% get list of company scripts
scripts = {k:v for k,v in company.__dict__.items() if isinstance(v, types.ModuleType) and v.__name__.startswith('company')}

#%% run through all company scripts to get jobs data
status = {'api_errors':[]}
jobs = {'dict':pool_getjobs(scripts)}

#%% retry those that failed
attempt = 1
while status['api_errors'] and attempt<=3:
    print(f"Retrying attempt {attempt}: {sorted([i[0] for i in status['api_errors']])}")
    jobs['dict'].update(retry_getjobs({k:v for k,v in scripts.items() if k in [i[0] for i in status['api_errors']]}))
    attempt += 1

#%% parse jobs dict to dataframe
jobs['dataframe'] = pd.DataFrame.from_dict({v1:jobs['dict'][k1][v1] for k1 in jobs['dict'].keys() for v1 in jobs['dict'][k1].keys()},
                                           orient='index')

jobs['dataframe'] = jobs['dataframe'].reset_index().rename(columns={'index':'URL'})

# some companies are split into multiple sources. combine all to same company name by splitting out separator.
jobs['dataframe']['Company'] = jobs['dataframe']['Company'].str.split('_').str[0]
jobs['dataframe'] = jobs['dataframe'][cols['jobs']].sort_values(by=['Company','Title'], key=lambda x:x.str.lower())
jobs['dataframe'] = jobs['dataframe'].reset_index(drop=True)

jobs['summary'] = summarize(jobs['dataframe'])
jobs['dataframe'] = jobs['dataframe'].drop(['Date Scraped'], axis=1) # same info in summary, don't need in all

print(f"{jobs['summary']['Number of Job Postings'].sum():,} job opportunities from {len(jobs['summary'])} companies")

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
    scrape_funcs.save_xlsx({'All':jobs['dataframe'], 'Summary':jobs['summary']}, files['export'].replace('_{date}', ''))

#%% export to google sheets (doesn't matter if errors exist)
g_sheets.auth(files['g_sheets_key'])
g_sheets.update(df=jobs['dataframe'], g_sheet_key='1NuJjghe752QkHOe92w3OtQs6wfO0e74l_HQxZkW9YSs', sheet_name='All')
g_sheets.update(df=jobs['summary'], g_sheet_key='1NuJjghe752QkHOe92w3OtQs6wfO0e74l_HQxZkW9YSs', sheet_name='Summary')