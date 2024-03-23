import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':100, # 100 is hard limit

        'requests':{'url':{'normalized_country_code[]':['SGP'],
                           'offset':0}}}

meta['requests']['url']['result_limit'] = meta['job_max']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        data_dict[meta['urls']['job']+i['job_path']] = {'Title':i['title'],
                                                        'Job Function':i['job_category'],
                                                        'Location':i['location']}
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'], json_decode=True)

    num_jobs = response['hits']
    pagesize = meta['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(response['jobs']) # parse first page

    # compile subsequent pages
    for i in range(pages-1):
        meta['requests']['url']['offset'] = meta['requests']['url']['offset'] + pagesize
        response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'], json_decode=True)
        jobs_dict.update(jobs(response['jobs']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)