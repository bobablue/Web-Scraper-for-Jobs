import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':100, # max, unable to change

        'requests':{'headers':{'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0'},
                    'url':{'location':['singapore'], 'format':'json', 'data_format':'detail', 'page':1}}}

meta['requests']['url']['per_page'] = meta['job_max']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(data):
    data_dict = {}
    for i in data:
        url_id = f"{i['talemetry_job_id']}-{i['permalink']}"
        data_dict[meta['urls']['job']+url_id] = {'Title':i['title'],
                                                 'Job Function':i['cfml3'],
                                                 'Location':i['location']['country']}
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], headers=meta['requests']['headers'],
                                 params=meta['requests']['url'])

    # happens too many times to not build an exception for... weak.
    if 'just a moment' in response.text.lower():
        return({})

    response = response.json()

    if response['total_entries']==0:
        return({})

    num_jobs = response['total_entries']
    pagesize = len(response['entries'])
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(response['entries']) # parse first page

    # compile subsequent pages
    for i in range(2, pages+1):
        meta['requests']['url']['page'] = i
        response = scrape_funcs.pull('get', url=meta['urls']['page'], headers=meta['requests']['headers'],
                                     params=meta['requests']['url'], json_decode=True)

        jobs_dict.update(jobs(response['entries']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)