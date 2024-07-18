import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'headers':{'tz':'GMT+08:00'},

                    # location:singapore; start from page 1
                    'json':{'filterSelectionParam':{'searchFilterSelections':[{'id':'LOCATION', 'selectedValues':['160422287']}]},
                            'pageNo':1}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        data_dict[meta['urls']['job'] + i['contestNo']] = {'Title':i['column'][0].strip(),
                                                           'Job Function':i['column'][0].split(',')[-1].strip(),
                                                           'Location':''.join([c for c in i['column'][1] if c not in ['"','[',']']])}

    # if title does not contain function (i.e., title==job function), then leave job function blank
    for i,j in data_dict.items():
        if j['Title']==j['Job Function']:
            j['Job Function'] = None

    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('post', json_decode=True, url=meta['urls']['page'],
                                 headers=meta['requests']['headers'], json=meta['requests']['json'])

    num_jobs = response['pagingData']['totalCount']
    pagesize = response['pagingData']['pageSize']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(response['requisitionList']) # parse first page

    # compile subsequent pages
    page_info = scrape_funcs.gen_page_info(params=meta['requests']['json'],
                                           page_range=range(2, pages+1),
                                           page_param='pageNo',
                                           multiplier=1)

    responses = scrape_funcs.concurrent_pull('post', url=meta['urls']['page'], headers=meta['requests']['headers'],
                                             json=page_info, json_decode=True)

    for v in responses.values():
        jobs_dict.update(jobs(v['requisitionList']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)