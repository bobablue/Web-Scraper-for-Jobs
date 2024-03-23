import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'url':{'location':['Singapore, Singapore'], 'page':1}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        data_dict[meta['urls']['job']+i['external_id']] = {'Title':i['text'],
                                                           'Job Function':i['lever_team'],
                                                           'Location':i['location']}

    data_dict = scrape_funcs.clean_loc(data_dict)
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'], json_decode=True)

    num_jobs = response['info']['postings']['total_result_count']
    pagesize = response['info']['postings']['per_page']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(response['records']['postings']) # parse first page

    # compile subsequent pages
    for i in range(2, pages+1):
        meta['requests']['url']['page'] = i
        response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'], json_decode=True)
        jobs_dict.update(jobs(response['records']['postings']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)