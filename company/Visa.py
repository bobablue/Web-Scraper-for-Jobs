import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':10, # 10 default, cannot be changed

        'requests':{'json':{'city':['Singapore'], 'from':0, 'size':None}}}

meta['requests']['json']['size'] = meta['job_max']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(data):
    data_dict = {}
    for i in data:
        data_dict[meta['urls']['job']+i['refNumber']] = {'Title':i['jobTitle'],
                                                         'Job Function':i['function'],
                                                         'Location':i['country']}
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('post', url=meta['urls']['page'], json=meta['requests']['json'], json_decode=True)

    num_jobs = response['recordsMatched']
    pagesize = meta['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(response['jobDetails']) # parse first page

    # compile subsequent pages
    for i in range(1,pages):
        meta['requests']['json']['from'] = i * pagesize
        response = scrape_funcs.pull('post', url=meta['urls']['page'], json=meta['requests']['json'], json_decode=True)
        jobs_dict.update(jobs(response['jobDetails']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)