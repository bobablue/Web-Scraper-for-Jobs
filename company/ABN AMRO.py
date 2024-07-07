import os
import datetime
from concurrent.futures import ThreadPoolExecutor
import copy

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'locations':['singapore'],

        'requests':{'url':{'sort':'created', 'sortDir':'DESC', 'pageNumber':1},

                    'headers':{'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:127.0) Gecko/20100101 Firefox/127.0',
                               'X-Requested-With':'XMLHttpRequest'}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        data_dict[meta['urls']['job'] + str(i['id'])] = {'Title':i['title'], 'Location':i['city']}

    data_dict = scrape_funcs.restrict_loc(data_dict, meta['locations'])
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], headers=meta['requests']['headers'],
                                 params=meta['requests']['url'], json_decode=True)

    num_jobs = response['meta']['num_total_hits']
    pagesize = response['meta']['maxPerPage']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(response['vacancies']) # parse first page

    # compile subsequent pages
    responses = {}
    with ThreadPoolExecutor(max_workers=min(os.cpu_count()*10, pages)) as executor:
        for i in range(2, pages+1):
            params = copy.deepcopy(meta['requests']['url'])
            params['pageNumber'] = i
            responses[i] = executor.submit(scrape_funcs.pull, 'get', url=meta['urls']['page'],
                                           headers=meta['requests']['headers'], params=params,
                                           json_decode=True)

        responses = {k:v.result() for k,v in responses.items()}

    for k,v in responses.items():
        jobs_dict.update(jobs(v['vacancies']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)