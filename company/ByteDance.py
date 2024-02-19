import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':1000,

        'requests':{'cookie':{'channel':'overseas',
                              'atsx-csrf-token':None},

                    'headers':{'x-csrf-token':None},

                    'post':{'location_code_list':['CT_163'], 'offset':0}}}

meta['requests']['post']['limit'] = meta['job_max']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        data_dict[meta['urls']['job'].replace('{id}',i['id'])] = {'Title':i['title'],
                                                                  'Job Function':i['job_category']['en_name'],
                                                                  'Location':i['city_info']['en_name']}
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    # get token and update cookie and headers data
    token = scrape_funcs.pull('post', url=meta['urls']['cookie'], json_decode=True)
    meta['requests']['cookie']['atsx-csrf-token'] = token['data']['token']
    meta['requests']['headers']['x-csrf-token'] = token['data']['token']

    # get jobs json data
    response = scrape_funcs.pull('post', url=meta['urls']['page'],
                                 headers=meta['requests']['headers'], cookies=meta['requests']['cookie'],
                                 json=meta['requests']['post'], json_decode=True)

    num_jobs = response['data']['count']
    pagesize = meta['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(response['data']['job_post_list']) # parse first page

    # get subsequent pages, if any
    for pg in range(1,pages):
        meta['requests']['post']['offset'] = pg * pagesize
        response = scrape_funcs.pull('post', url=meta['urls']['page'],
                                     headers=meta['requests']['headers'], cookies=meta['requests']['cookie'],
                                     json=meta['requests']['post'], json_decode=True)

        jobs_dict.update(jobs(response['data']['job_post_list']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)