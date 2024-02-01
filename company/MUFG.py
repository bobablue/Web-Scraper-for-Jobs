import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        # singapore; 20 is hard limit so need to loop
        'requests':{'post':{'appliedFacets':{'Country':['80938777cac5440fab50d729f9634969']}, 'offset':0, 'limit':20}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_dict):
    data_dict = {}
    data_dict[meta['urls']['job']+json_dict['externalPath']] = {'Title':json_dict['title'],
                                                                'Location':json_dict['locationsText']}

    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    # get total number of jobs and pages to loop through and parse first page of results
    response = scrape_funcs.pull('post', json_decode=True, url=meta['urls']['page'], json=meta['requests']['post'])

    num_jobs = response['total']
    pagesize = len(response['jobPostings'])
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = {}
    for i in response['jobPostings']:
        jobs_dict.update(jobs(i))

    # compile jobs from all pages after first, into main dict (update offset number in meta['requests']['post'])
    for pg in range(pages):
        meta['requests']['post']['offset'] = (pg+1) * pagesize
        response = scrape_funcs.pull('post', json_decode=True, url=meta['urls']['page'], json=meta['requests']['post'])

        for i in response['jobPostings']:
            jobs_dict.update(jobs(i))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)