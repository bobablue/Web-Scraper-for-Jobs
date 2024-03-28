"""Create your own keyword filters using this script."""
import os
import pandas as pd

from util import scrape_funcs

#%% static data
folders = {'archive':'archive', 'export':os.getcwd()}

files = {'export_suffix':'Filtered'}
files['export'] = f"Job Opportunities_{files['export_suffix']}.xlsx"

# get list of archived files and sort by timestamp
files['archive'] = sorted([os.path.join(folders['archive'], i) for i in os.listdir(folders['archive']) if i.startswith('Job Opportunities')])

# keywords to filter job titles on
jobs = {'keywords':['analy','data'],
        'exclude':['intern']}

#%% functions
#%%
def filter_df(df, keywords=jobs['keywords'], exclude=jobs['exclude']):
    f_df = df.copy()
    f_df = f_df[f_df['Title'].str.lower().str.contains('|'.join(keywords))]
    f_df = f_df[~f_df['Title'].str.lower().str.contains('|'.join(exclude))]
    return(f_df)

#%% get new roles from last vs penultimate using URL as key
def show_new(last_df, penult_df):
    new_urls = set(last_df['URL']) - set(penult_df['URL'])
    new_df = last_df[last_df['URL'].isin(new_urls)]
    return(new_df)

#%% get latest list of jobs
jobs = {'all':pd.read_excel(files['export'].replace(f"_{files['export_suffix']}", ''))}

#%% compare latest filtered list with 2nd latest to see new roles posted
jobs['filtered_latest'] = filter_df(jobs['all'])

jobs['filtered_penultimate'] = pd.read_excel(files['archive'][-1])
jobs['filtered_penultimate'] = filter_df(jobs['filtered_penultimate'])

jobs['new'] = show_new(jobs['filtered_latest'], jobs['filtered_penultimate'])

print(f"{len(jobs['new'])} new jobs")

#%% export data
list_dfs = {'New':jobs['new'], 'Filtered':jobs['filtered_latest'], 'All':jobs['all']}
scrape_funcs.save_xlsx(list_dfs, os.path.join(folders['export'], files['export']))