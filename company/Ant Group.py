import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'post':{'regions':'SINGAPORE',
                            'language':'en',
                            'pageSize':50, # 50 is max page size
                            'pageIndex':1}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    # job function missing in some posts
    if json_obj['categories'] is None:
        job_func = ''
    else:
        job_func = ', '.join(json_obj['categories'])

    data_dict = {}
    data_dict[meta['urls']['job']+str(json_obj['id'])] = {'Title':json_obj['name'],
                                                          'Location':', '.join(json_obj['workLocations']),
                                                          'Job Function':job_func}
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('post', url=meta['urls']['page'], json=meta['requests']['post'], json_decode=True)

    jobs_dict = {}
    for i in response['content']:
        jobs_dict.update(jobs(i))

    num_jobs = response['totalCount']
    pagesize = response['pageSize']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    # compile jobs from all pages after first, into main dict (update post_data to include page number)
    for pg in range(2, pages+1):
        meta['requests']['post']['pageIndex'] = pg
        response = scrape_funcs.pull('post', url=meta['urls']['page'], json=meta['requests']['post'], json_decode=True)

        for i in response['content']:
            jobs_dict.update(jobs(i))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)