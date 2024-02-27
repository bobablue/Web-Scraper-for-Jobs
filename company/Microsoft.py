import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':20, # 20 is max size

        'requests':{'url':{'lc':'Singapore', 'pg':1}}}

meta['requests']['url']['pgSz'] = meta['job_max']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_dict):
    data_dict = {}
    for i in json_dict:
        data_dict[meta['urls']['job'] + i['jobId']] = {'Title':i['title'],
                                                       'Job Function':i['properties']['discipline'],
                                                       'Location':i['properties']['primaryLocation']}
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'], json_decode=True)

    num_jobs = response['operationResult']['result']['totalJobs']
    pagesize = meta['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(response['operationResult']['result']['jobs']) # parse first page

    for i in range(2,pages+1):
        meta['requests']['url']['pg'] = i
        response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'], json_decode=True)
        jobs_dict.update(jobs(response['operationResult']['result']['jobs']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)