import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':1000,

        'requests':{'url':{'countryId':11, 'pageSize':None, 'pageIndex':1}}}

meta['requests']['url']['pageSize'] = meta['job_max']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        data_dict[i['PostURL']] = {'Title':i['RecruitPostName'],
                                   'Job Function':i['CategoryName'],
                                   'Location':i['CountryName']}
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'],
                                 params=meta['requests']['url'], json_decode=True)

    # update if number of jobs is greater than default, then pull again
    if (num_jobs:=response['Data']['Count']) > meta['job_max']:
        meta['job_max'] = num_jobs
        response = scrape_funcs.pull('get', url=meta['urls']['page'],
                                     params=meta['requests']['url'], json_decode=True)

    jobs_dict = jobs(response['Data']['Posts'])
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)