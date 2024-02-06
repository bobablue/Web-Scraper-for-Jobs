import os
import shutil
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import types

import company

#%% static data
folders = {'company':'company', 'archive':'archive'}
files = {'export':'Job Opportunities_{date}.xlsx'}
cols = {'jobs':['Company', 'Title', 'URL', 'Location', 'Job Function', 'Date Scraped']}

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

#%% save a list of dataframes into a single excel workbook
def save_xlsx(list_dfs, filename):
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        for ws,df in list_dfs.items():
            index = df.index.nlevels if df.index.nlevels>1 else 0
            df.to_excel(writer, sheet_name=ws, index=False, freeze_panes=(1,0))
            writer.sheets[ws].autofilter(*[df.columns.nlevels-1, 0, df.columns.nlevels-1, index+len(df.columns)-1])

#%% get list of company scripts
scripts = {k:v for k,v in company.__dict__.items() if isinstance(v, types.ModuleType) and v.__name__.startswith('company')}

#%% run through all company scripts to get jobs data
jobs = {'dict':pool_getjobs(scripts)}

#%% parse jobs dict to dataframe
jobs['dataframe'] = pd.DataFrame.from_dict({v1:jobs['dict'][k1][v1] for k1 in jobs['dict'].keys() for v1 in jobs['dict'][k1].keys()},
                                           orient='index')

jobs['dataframe'] = jobs['dataframe'].reset_index().rename(columns={'index':'URL'})
jobs['dataframe'] = jobs['dataframe'][cols['jobs']].sort_values(by=['Company','Location','Title']).reset_index(drop=True)

#%% filters
#%% keyword filters on job titles, show latest
jobs['keywords'] = ['analy','data','economi','model','python','risk','scien']
jobs['exclude'] = ['intern','summer','graduate']

jobs['filtered'] = jobs['dataframe'][jobs['dataframe']['Title'].str.lower().str.contains('|'.join(jobs['keywords']))]
jobs['filtered'] = jobs['filtered'][~jobs['filtered']['Title'].str.lower().str.contains('|'.join(jobs['exclude']))]

#%% show only new (filtered) jobs since the last update using URL as key
# rename current latest file by adding max(date scraped) to file name, then move file to archive
if os.path.isfile(i:=files['export'].replace('_{date}','')):
    jobs['previous'] = pd.read_excel(i, sheet_name='Filtered')
    shutil.move(i, os.path.join(folders['archive'], files['export'].replace('{date}', get_file_date(i))))

else:
    jobs['previous'] = pd.DataFrame(columns=cols['jobs'])

jobs['new'] = jobs['filtered'][jobs['filtered']['URL'].isin(set(jobs['filtered']['URL']) - set(jobs['previous']['URL']))].copy()
print(f"{len(jobs['new'])} new jobs")

#%% export data
list_dfs = {'New':jobs['new'], 'Filtered':jobs['filtered'], 'All':jobs['dataframe']}
save_xlsx(list_dfs, files['export'].replace('_{date}', ''))