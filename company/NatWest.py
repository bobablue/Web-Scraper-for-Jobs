import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'job_max':1000,
                    'url':{'location':['singapore'], 'format':'json', 'data_format':'detail', 'page':1}}}

meta['requests']['url']['per_page'] = meta['requests']['job_max']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(data):
    data_dict = {}
    for i in data:
        url_id = f"{i['talemetry_job_id']}-{i['permalink']}"
        data_dict[meta['urls']['job']+url_id] = {'Title':i['title'],
                                                 'Job Function':i['cfml3'],
                                                 'Location':i['location']['country']}
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'], json_decode=True)

    # assume num_jobs would not be >1,000, but check just in case
    num_jobs = response['total_entries']
    if num_jobs>meta['requests']['job_max']:
        raise ValueError(f"Number of posted jobs greater than defined max: {num_jobs}\nCheck how to pull all")

    jobs_dict = jobs(response['entries'])
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)