import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':50, # 50 is max page size

        'requests':{'headers':{'Referer':'https://talent.antgroup.com/'},

                    'post':{'regions':'SINGAPORE',
                            'language':'en',
                            'pageSize':None,
                            'pageIndex':1}}}

meta['requests']['post']['pageSize'] = meta['job_max']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:

        # job function missing in some posts
        if i['categories'] is None:
            job_func = ''
        else:
            job_func = ', '.join(i['categories'])

        data_dict[meta['urls']['job']+str(i['id'])] = {'Title':i['name'],
                                                       'Location':', '.join(i['workLocations']),
                                                       'Job Function':job_func}
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('post', url=meta['urls']['page'], headers=meta['requests']['headers'],
                                 json=meta['requests']['post'], json_decode=True)

    num_jobs = response['totalCount']
    pagesize = response['pageSize']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(response['content']) # parse first page

    # compile subsequent pages
    page_info = scrape_funcs.gen_page_info(params=meta['requests']['post'],
                                           page_range=range(2, pages+1),
                                           page_param='pageIndex',
                                           multiplier=1)

    responses = scrape_funcs.concurrent_pull('post', url=meta['urls']['page'], headers=meta['requests']['headers'],
                                             json=page_info, json_decode=True)

    for v in responses.values():
        jobs_dict.update(jobs(v['content']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)