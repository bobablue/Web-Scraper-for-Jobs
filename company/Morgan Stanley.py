import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'url':{'Country':'Singapore', 'start':0}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        data_dict[meta['urls']['job'] + str(i['id'])] = {'Title':i['name'],
                                                         'Location':i['location'],
                                                         'Job Function':i['department']}

    data_dict = scrape_funcs.clean_loc(data_dict)
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', json_decode=True, url=meta['urls']['page'], params=meta['requests']['url'])

    num_jobs = response['count']
    pagesize = len(response['positions'])
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(response['positions'])

    # compile subsequent pages
    for i in range(1, pages):
        meta['requests']['url']['start'] = i * 10
        response = scrape_funcs.pull('get', json_decode=True, url=meta['urls']['page'], params=meta['requests']['url'])
        jobs_dict.update(jobs(response['positions']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)