import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'locations':['singapore'],
        'job_max':20, # 20 is hard limit

        'requests':{'post':{'limit':None, 'offset':0}}}

meta['requests']['post']['limit'] = meta['job_max']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        data_dict[meta['urls']['job']+i['externalPath']] = {'Title':i['title'], 'Location':i['locationsText']}
        data_dict = scrape_funcs.clean_loc(data_dict)

    # restrict to selected locations
    data_dict = scrape_funcs.restrict_loc(data_dict, meta['locations'])
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('post', url=meta['urls']['page'],
                                 json=meta['requests']['post'], json_decode=True)

    num_jobs = response['total']
    pagesize = len(response['jobPostings'])
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(response['jobPostings']) # parse first page

    # compile subsequent pages
    page_info = scrape_funcs.gen_page_info(params=meta['requests']['post'],
                                           page_range=range(1, pages),
                                           page_param='offset',
                                           multiplier=pagesize)

    responses = scrape_funcs.concurrent_pull('post', url=meta['urls']['page'], json=page_info, json_decode=True)

    for v in responses.values():
        jobs_dict.update(jobs(v['jobPostings']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)