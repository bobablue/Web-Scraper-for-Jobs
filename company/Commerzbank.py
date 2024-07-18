import os
import datetime
import re
import copy
from concurrent.futures import ThreadPoolExecutor

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':100,
        'locations':['singapore'],

        'requests':{'url':{'data':'{"SearchParameters":{"FirstItem":1,"CountItem":job_max,\
                                                        "Sort":[{"Criterion":"PublicationStartDate",\
                                                                 "Direction":"DESC"}]}}'}}}

meta['requests']['url']['data'] = meta['requests']['url']['data'].replace('job_max', str(meta['job_max']))

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        i = i['MatchedObjectDescriptor']
        data_dict[i['PositionURI']] = {'Title':i['PositionTitle'],
                                       'Job Function':i['JobCategory'][0]['Name'],
                                       'Location':i['OrganizationName']}

    # restrict to selected countries
    data_dict = scrape_funcs.restrict_loc(data_dict, meta['locations'])
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'], json_decode=True)

    num_jobs = response['SearchResult']['SearchResultCountAll']
    pagesize = meta['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(response['SearchResult']['SearchResultItems']) # parse first page

    # compile subsequent pages
    responses = {}
    with ThreadPoolExecutor(max_workers=min(os.cpu_count()*10, pages)) as executor:
        for i in range(1, pages+1):
            first_item = meta['job_max'] * i
            params = copy.deepcopy(meta['requests']['url'])
            params['data'] = re.sub(r'"FirstItem":(\d+)', f'"FirstItem":{first_item}', params['data'])
            responses[i] = executor.submit(scrape_funcs.pull, 'get', url=meta['urls']['page'],
                                           params=params, json_decode=True)

        responses = {k:v.result() for k,v in responses.items()}

    for v in responses.values():
        jobs_dict.update(jobs(v['SearchResult']['SearchResultItems']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)