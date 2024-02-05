import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'url':{'location':'Singapore', 'start':0}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    data_dict[meta['urls']['job']+str(json_obj['id'])] = {'Title':json_obj['name'],
                                                          'Location':json_obj['location'],
                                                          'Job Function':json_obj['department']}
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    # get total number of jobs and pages to loop through and parse first page of results
    response = scrape_funcs.pull('get', json_decode=True,
                                 url=meta['urls']['page'], params=meta['requests']['url'])

    num_jobs = response['count']
    pagesize = len(response['positions'])
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = {}
    for i in response['positions']:
        jobs_dict.update(jobs(i))

    # compile jobs from all pages after first, into main dict (update start number in meta['requests']['url'])
    for pg in range(2, pages+1):
        meta['requests']['url']['start'] = (pg-1) * 10
        response = scrape_funcs.pull('get', json_decode=True, url=meta['urls']['page'], params=meta['requests']['url'])
        for i in response['positions']:
            jobs_dict.update(jobs(i))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)