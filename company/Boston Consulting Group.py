import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':500,

        'requests':{'json':{'ddoKey':'refineSearch',
                            'from':0,
                            'size':None,
                            'jobs':'true',
                            'selected_fields':{'country':['Singapore']}}}}

meta['requests']['json']['size'] = meta['job_max']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        data_dict[meta['urls']['job'] + i['jobId']] = {'Title':i['title'],
                                                       'Location':i['country'],
                                                       'Job Function':i['category']}
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    cookie = scrape_funcs.pull('get', url=meta['urls']['cookie']).cookies.get_dict()

    response = scrape_funcs.pull('post', json_decode=True, url=meta['urls']['page'],
                                 json=meta['requests']['json'], cookies=cookie)

    num_jobs = response['refineSearch']['totalHits']
    pagesize = response['refineSearch']['hits']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(response['refineSearch']['data']['jobs']) # parse first page

    # compile subsequent pages
    for i in range(1,pages):
        meta['requests']['json']['from'] = i * pagesize
        response = scrape_funcs.pull('post', json_decode=True, url=meta['urls']['page'],
                                     json=meta['requests']['json'], cookies=cookie)

        jobs_dict.update(jobs(response['refineSearch']['data']['jobs']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)