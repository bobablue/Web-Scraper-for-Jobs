import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        # 20 is limit
        'requests':{'job_max':20,
                    'json':{'appliedFacets':{'locationCountry':['80938777cac5440fab50d729f9634969']},
                            'offset':0}}}

meta['requests']['json']['limit'] = meta['requests']['job_max']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(data):
    data_dict = {}
    for i in data:
        data_dict[meta['urls']['job']+i['externalPath']] = {'Title':i['title'],
                                                            'Location':i['locationsText']}
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('post', url=meta['urls']['page'], json=meta['requests']['json'], json_decode=True)

    num_jobs = response['total']
    pagesize = meta['requests']['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(response['jobPostings']) # parse first page

    # compile jobs from all pages after first, into main dict
    for pg in range(1, pages):
        meta['requests']['json']['offset'] = pg * meta['requests']['job_max']
        response = scrape_funcs.pull('post', url=meta['urls']['page'], json=meta['requests']['json'], json_decode=True)
        jobs_dict.update(jobs(response['jobPostings']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)