import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'locations':['singapore']}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        data_dict[i['absolute_url']] = {'Title':i['title'],
                                        'Job Function':i['departments'][0]['name'],
                                        'Location':i['location']['name']}

    # keep only selected locations
    data_dict = {k:v for k,v in data_dict.items() if v['Location'].lower() in meta['locations']}
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    # get all jobs, then filter
    response = scrape_funcs.pull('get', url=meta['urls']['page'], json_decode=True)
    jobs_dict = jobs(response['jobs'])
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)