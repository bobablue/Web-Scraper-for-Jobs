import os
import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import types

import company

#%% static data
meta = {'folder':'company',
        'export_file':'Job Opportunities.xlsx',
        'cols_jobs':['Company', 'Title', 'URL', 'Location', 'Job Function', 'Date Scraped']}

#%% functions
#%%
def pool_getjobs(list_scripts):
    jobs = {}
    with ThreadPoolExecutor(max_workers=min(os.cpu_count()*5, len(list_scripts))) as executor:
        for i in list_scripts:
            jobs[i] = executor.submit(list_scripts[i].get_jobs)
    jobs = {k:v.result() for k,v in jobs.items()}
    return(jobs)

#%% get list of company scripts
scripts = {k:v for k,v in company.__dict__.items() if isinstance(v, types.ModuleType) and v.__name__ not in ['os']}

#%% run through all company scripts to get jobs data
jobs = pool_getjobs(scripts)