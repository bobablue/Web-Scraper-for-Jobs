import os
import datetime
import json

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':500, # 500 is hard limit

        'requests':{'url':{'stateCity':['SG'],
                           'Limit':None,
                           'Organization':2062,
                           'callback':'jobsCallback',
                           'offset':1}}}

meta['requests']['url']['Limit'] = meta['job_max']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        data_dict[i['url']] = {'Title':i['title'], 'Job Function':i['sub_category'], 'Location':i['primary_country']}
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    # response loads a JSONP object, so need to remove padding
    response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'])
    idx = {'start':response.text.find('('), 'end':response.text.rfind(')')}
    json_obj = json.loads(response.text[idx['start']+1:idx['end']])

    num_jobs = json_obj['totalHits']
    pagesize = meta['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(json_obj['queryResult']) # parse first page

    # compile subsequent pages, if any
    for i in range(pages-1):
        meta['requests']['url']['offset'] = meta['requests']['url']['offset'] + meta['job_max']
        response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'])
        idx = {'start':response.text.find('('), 'end':response.text.rfind(')')}
        json_obj = json.loads(response.text[idx['start']+1:idx['end']])

        jobs_dict.update(jobs(json_obj['queryResult']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)