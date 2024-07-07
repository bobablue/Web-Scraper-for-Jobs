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
def collapse_list_dict(obj):
    coll = [x for v in [list(i.values()) for i in obj] for x in v]
    coll = ' | '.join(coll)
    return(coll)

#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data = json_obj['result']['pageContext']['data']['allGreenhouseDepartment']['nodes']
    jobs_all = {}

    # jobs found in ['jobs'] and ['parent']['jobs'] but they overlap so don't need to capture ['parent']['jobs']
    for i in data:

        if i['jobs']:
            for j in i['jobs']:
                jobs_all[j['absolute_url']] = {'Title':j['title'],
                                               'Job Function':collapse_list_dict(j['departments']),
                                               'Location':j['location']['name']}

    jobs_filtered = scrape_funcs.restrict_loc(jobs_all, meta['locations'])
    return(jobs_filtered)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], json_decode=True)
    jobs_dict = jobs(response)
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)