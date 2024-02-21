import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'json':{'ddoKey':'refineSearch',
                            'from':0,
                            'size':500,
                            'jobs':'true',
                            'selected_fields':{'country':['Singapore']}}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    data_dict[f"{meta['urls']['job']}{json_obj['jobId']}"] = {'Title':json_obj['title'],
                                                              'Location':json_obj['country'],
                                                              'Job Function':json_obj['subCategory']}
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    cookie = scrape_funcs.pull('get', url=meta['urls']['cookie']).cookies.get_dict()

    # get first batch of jobs (max 500 per call)
    response = scrape_funcs.pull('post', json_decode=True, url=meta['urls']['page'],
                                 json=meta['requests']['json'], cookies=cookie)

    num_jobs = response['refineSearch']['totalHits']
    pagesize = response['refineSearch']['hits']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    # parse first page
    jobs_dict = {}
    for i in response['refineSearch']['data']['jobs']:
        jobs_dict.update(jobs(i))

    # compile jobs from all pages after first, into main dict (update from in post_data)
    for pg in range(pages-1):
        meta['requests']['json']['from'] = (pg+1) * pagesize
        response = scrape_funcs.pull('post', json_decode=True, url=meta['urls']['page'],
                                     json=meta['requests']['json'], cookies=cookie)

        for i in response['refineSearch']['data']['jobs']:
            jobs_dict.update(jobs(i))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)