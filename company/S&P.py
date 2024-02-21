import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':100,

        'requests':{'url':{'location':'Singapore', 'page':1}}}

meta['requests']['url']['limit'] = meta['job_max']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(data):
    data_dict = {}
    for i in data:
        i = i['data']
        data_dict[i['meta_data']['canonical_url']] = {'Title':i['title'],
                                                      'Job Function':', '.join([x.strip() for x in i['category']]),
                                                      'Location':i['country']}
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'],
                                 params=meta['requests']['url'], json_decode=True)

    num_jobs = response['totalCount']
    pagesize = meta['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(response['jobs']) # parse first page

    # compile jobs from all pages after first, into main dict (update start from in requests params)
    for pg in range(2,pages+1):
        meta['requests']['url']['page'] = pg
        response = scrape_funcs.pull('get', url=meta['urls']['page'],
                                     params=meta['requests']['url'], json_decode=True)

        jobs_dict.update(jobs(response['jobs']))
        print(pg, len(jobs_dict))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)