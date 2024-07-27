import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':10, # default pagesize, cannot be changed

        'requests':{'url':{'location':'singapore', 'start':0, 'num':None}}}

meta['requests']['url']['num'] = meta['job_max']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        data_dict[i['canonicalPositionUrl']] = {'Title':i['name'], 'Job Function':i['department'], 'Location':i['location']}
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'], json_decode=True)

    num_jobs = response['count']
    pagesize = meta['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(response['positions']) # parse first page

    # compile subsequent pages
    page_info = scrape_funcs.gen_page_info(params=meta['requests']['url'],
                                           page_range=range(1, pages),
                                           page_param='start',
                                           multiplier=pagesize)

    responses = scrape_funcs.concurrent_pull('get', url=meta['urls']['page'], params=page_info, json_decode=True)

    for v in responses.values():
        jobs_dict.update(jobs(v['positions']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)