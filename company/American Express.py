import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        # 10 is default pagesize and cannot be changed
        'requests':{'url':{'location':'Singapore', 'domain':'aexp.com', 'start':0, 'num':10}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(data):
    data_dict = {}
    for i in data:
        data_dict[i['canonicalPositionUrl']] = {'Title':i['name'],
                                                'Job Function':i['department'],
                                                'Location':i['location']}

    data_dict = scrape_funcs.clean_loc(data_dict)
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'],
                                 params=meta['requests']['url'], json_decode=True)

    no_jobs = response['count']
    pagesize = meta['requests']['url']['num']
    pages = no_jobs//pagesize + (no_jobs % pagesize>0)

    # parse first page
    jobs_dict = jobs(response['positions'])

    # compile jobs from all pages after first, into main dict (update start from in requests params)
    for pg in range(1,pages):
        meta['requests']['url']['start'] = (pg) * pagesize
        response = scrape_funcs.pull('get', url=meta['urls']['page'],
                                     params=meta['requests']['url'], json_decode=True)

        jobs_dict.update(jobs(response['positions']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)