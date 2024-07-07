import os
import datetime
import re

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':330,
        'locations':['singapore'],

        'requests':{'url':{'data':'{"SearchParameters":{"FirstItem":1,"CountItem":job_max}}'}}}

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

    # restrict to singapore only
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

    for i in range(1,pages):
        first_item = (meta['job_max'] * i) + 1
        meta['requests']['url']['data'] = re.sub(r'"FirstItem":(\d+)', f'"FirstItem":{first_item}', meta['requests']['url']['data'])
        response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'], json_decode=True)
        jobs_dict.update(jobs(response['SearchResult']['SearchResultItems']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)