import os
import datetime
from concurrent.futures import ThreadPoolExecutor

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'json':{'page':1, 'locale':'en-sg',
                            'filters':{'postingpostLocation':['postLocation-SGP']}}}}

#%% functions
#%%
def get_token(url):
    response = scrape_funcs.pull('get', url=url)
    token = {'cookies':response.cookies.get_dict(),
             'headers':{'X-Apple-CSRF-Token':response.headers['x-apple-csrf-token']}}
    return(token)

#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        data_dict[meta['urls']['job'] + i['positionId']] = {'Title':i['postingTitle'],
                                                            'Job Function':i['team']['teamName'],
                                                            'Location':i['locations'][0]['name']}
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    # get first page
    token = get_token(meta['urls']['cookie'])
    response = scrape_funcs.pull('post', url=meta['urls']['page'], json=meta['requests']['json'],
                                 json_decode=True, **token)

    num_jobs = response['totalRecords']
    pagesize = len(response['searchResults'])
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(response['searchResults']) # parse first page

    # compile subsequent pages
    page_info = {}
    for i in range(2, pages+1):
        page_info[i] = get_token(meta['urls']['cookie'])
        page_info[i].update({'json':meta['requests']['json'].copy()})
        page_info[i]['json']['page'] = i

    responses = {}
    with ThreadPoolExecutor(max_workers=len(page_info)) as executor:
        for i in page_info:
            responses[i] = executor.submit(scrape_funcs.pull, 'post', url=meta['urls']['page'],
                                           json_decode=True, **page_info[i])

        responses = {k:v.result() for k,v in responses.items()}

    for v in responses.values():
        jobs_dict.update(jobs(v['searchResults']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)