import os
import copy
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':1000,

        # not sure if any url params would change over time
        'requests':{'url':{'x-algolia-agent':'Algolia%20for%20JavaScript%20(4.14.2)%3B%20Browser%20(lite)%3B%20instantsearch.js%20(4.49.1)%3B%20JS%20Helper%20(3.11.1)',
                           'x-algolia-api-key':'99b47a20ffdeba0849e08052a915060a',
                           'x-algolia-application-id':'EOIG7V0A2O'},

                    'post':{'requests':[{'indexName':'CAREERS_prod',

                                         'params':{'facetFilters':'["location_APAC:Singapore"]',
                                                   'hitsPerPage':None, 'page':0}}]}}}

meta['requests']['post']['requests'][0]['params']['hitsPerPage'] = meta['job_max']

#%% functions
#%%
def params_to_str(params_obj):
    stringed = copy.deepcopy(params_obj)
    stringed['requests'][0]['params'] = '&'.join([f"{k}={v}" for k,v in stringed['requests'][0]['params'].items()])
    return(stringed)

#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(data):
    data_dict = {}
    for i in data:

        data_dict[i['absolute_url']] = {'Title':i['title'],
                                        'Job Function':i['team'] if 'team' in i else i['department'],
                                        'Location':i['location_string']}

    data_dict = scrape_funcs.clean_loc(data_dict)
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('post', url=meta['urls']['page'], params=meta['requests']['url'],
                                 json=params_to_str(meta['requests']['post']), json_decode=True)

    json_obj = response['results'][0]

    num_jobs = json_obj['nbHits']
    pagesize = meta['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(json_obj['hits']) # parse first page

    # compile subsequent pages
    for i in range(1,pages):
        meta['requests']['post']['requests'][0]['params']['page'] = i
        response = scrape_funcs.pull('post', url=meta['urls']['page'], params=meta['requests']['url'],
                                     json=params_to_str(meta['requests']['post']), json_decode=True)

        json_obj = response['results'][0]
        jobs_dict.update(jobs(json_obj['hits']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)