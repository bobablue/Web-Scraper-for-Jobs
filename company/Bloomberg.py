import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'job_max':2500,
                    'url':{'searchQueryString':'lc=Singapore&nr=job_max'},

                    'headers':{'X-Requested-With':'XMLHttpRequest'}}}

# 2,500 is max page size
meta['requests']['url']['searchQueryString'] = meta['requests']['url']['searchQueryString'].replace('job_max', str(meta['requests']['job_max']))

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(data):
    data_dict = {}
    for i in data:
        data_dict[meta['urls']['job']+i['JobReqNbr']] = {'Title':i['JobTitle'],
                                                         'Job Function':i['Specialty']['Value'],
                                                         'Location':i['Office']['Country']}
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], json_decode=True,
                                 headers=meta['requests']['headers'], params=meta['requests']['url'])

    # assume num_jobs would not be >2,500, but check just in case
    num_jobs = int(response['totalJobCount'])
    if num_jobs>meta['requests']['job_max']:
        raise ValueError(f"Number of posted jobs greater than defined max: {num_jobs}\nCheck how to pull all")

    jobs_dict = jobs(response['jobData'])
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)