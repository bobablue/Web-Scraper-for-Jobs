import os
import shutil
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import types

import gspread
from google.oauth2.service_account import Credentials

import company
from util import check_urls, scrape_funcs

#%% static data
folders = {'company':'company', 'archive':'archive'}
files = {'export':'Job Opportunities_{date}.xlsx'}
cols = {'jobs':['Company', 'Title', 'URL', 'Location', 'Job Function', 'Date Scraped']}

# variables for google sheets API
gsheets = {'scope':['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive']}
gsheets['credentials'] = Credentials.from_service_account_file(r'config/gsheets_key.json', scopes=gsheets['scope'])
gsheets['auth'] = gspread.authorize(gsheets['credentials'])

#%% functions
#%% parallel requests
def pool_getjobs(list_scripts):
    jobs = {}
    with ThreadPoolExecutor(max_workers=min(os.cpu_count()*5, len(list_scripts))) as executor:
        for i in list_scripts:
            jobs[i] = executor.submit(list_scripts[i].get_jobs)
    jobs = {k:v.result() for k,v in jobs.items()}
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
jobs = {'dict':pool_getjobs(scripts)}

#%% parse jobs dict to dataframe
jobs['dataframe'] = pd.DataFrame.from_dict({v1:jobs['dict'][k1][v1] for k1 in jobs['dict'].keys() for v1 in jobs['dict'][k1].keys()},
                                           orient='index')

jobs['dataframe'] = jobs['dataframe'].reset_index().rename(columns={'index':'URL'})
jobs['dataframe'] = jobs['dataframe'][cols['jobs']].sort_values(by=['Company','Location','Title'], key=lambda x:x.str.lower())
jobs['dataframe'] = jobs['dataframe'].reset_index(drop=True)

print(f"{len(jobs['dataframe'])} job opportunities from {len(set(jobs['dataframe']['Company']))} companies")

#%% sample check if job URLs are valid. if status is 404, API has probably changed, so code needs an update.
status = {'all':check_urls.run_checks(jobs['dataframe'])}
status['errors'] = status['all'][status['all']['Status']!=200]
status['errors'] = dict(zip(status['errors']['Company'], status['errors']['Status']))
if status['errors']:
    print('URL errors:', status['errors'])

#%% archive current file before saving latest output
if os.path.isfile(i:=files['export'].replace('_{date}','')):
    shutil.move(i, os.path.join(folders['archive'], files['export'].replace('{date}', get_file_date(i))))

#%% export data locally and to google sheets
scrape_funcs.save_xlsx({'All':jobs['dataframe']}, files['export'].replace('_{date}', ''))

# google sheets
gsheets['wb'] = gsheets['auth'].open_by_key('1NuJjghe752QkHOe92w3OtQs6wfO0e74l_HQxZkW9YSs')

gsheets['dataframe'] = jobs['dataframe'].copy().fillna('')
gsheets['dataframe']['Date Scraped'] = gsheets['dataframe']['Date Scraped'].dt.strftime('%Y-%m-%d %H:%M:%S')

# https://docs.gspread.org/en/latest/api/models/worksheet.html#gspread.worksheet.Worksheet.update
gsheets['All'] = gsheets['wb'].worksheet('All')
gsheets['All'].clear()
gsheets['All'].update(range_name='',
                      values=[gsheets['dataframe'].columns.values.tolist()] + gsheets['dataframe'].values.tolist())