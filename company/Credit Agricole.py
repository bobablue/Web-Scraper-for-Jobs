import os
import datetime
import re

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':1000,

        'requests':{'cookie':{'rgpd':'{"stats":false}'},

                    'data':{'action':'get_offers', 'nonce':None, 'locationsList':169, 'page':1}}}

meta['requests']['data']['limit'] = meta['job_max']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        data_dict[i['link']] = {'Title':i['title'],
                                'Job Function':i['job']['label'],
                                'Location':i['country']['label']}

    data_dict = scrape_funcs.clean_loc(data_dict)
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    # get cookie and nonce to generate post data
    response = scrape_funcs.pull('post', url=meta['urls']['cookie'])
    meta['requests']['cookie'].update(response.cookies.get_dict())
    meta['requests']['data']['nonce'] = re.findall(r'data-nonce="(.+)"', response.text)[0]

    # get all jobs
    response = scrape_funcs.pull('post', url=meta['urls']['page'], cookies=meta['requests']['cookie'],
                                 data=meta['requests']['data'], json_decode=True)

    num_jobs = response['pagination']['total_elements_count']

    # if num_jobs>max_jobs, update url post data and call again with updated number
    if num_jobs>meta['requests']['data']['limit']:
        meta['requests']['data']['limit'] = num_jobs
        response = scrape_funcs.pull('post', url=meta['urls']['page'], cookies=meta['requests']['cookie'],
                                     data=meta['requests']['data'], json_decode=True)

    jobs_dict = jobs(response['elements'])
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)