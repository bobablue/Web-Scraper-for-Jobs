import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'finder':{'siteNumber':'CX_1', 'limit':None, 'locationId':'300000000229065'}, # singapore
                    'url':{'expand':'requisitionList.secondaryLocations,flexFieldsFacet.values', 'finder':None}}}

#%% functions
#%% update total number of jobs in various parameter objects
def update_nojobs(nojobs, finder, url):
    finder['limit'] = nojobs
    url['finder'] = f"findReqs;{','.join(f'{k}={v}' for k,v in finder.items())}"
    return(finder, url)

#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_dict):
    data_dict = {meta['urls']['job']+json_dict['Id']:{'Title':json_dict['Title'],
                                                      'Location':json_dict['PrimaryLocation']}}

    data_dict = scrape_funcs.clean_loc(data_dict)
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', json_decode=True,
                                 url=meta['urls']['page'], params=meta['requests']['url'])['items'][0]

    # if no_jobs>default in limit, update params and call again with updated number
    no_jobs = response['TotalJobsCount']
    if no_jobs>meta['requests']['finder']['limit']:
        meta['requests']['finder'], meta['requests']['url'] = update_nojobs(no_jobs,
                                                                            meta['requests']['finder'],
                                                                            meta['requests']['url'])

        response = scrape_funcs.pull('get', json_decode=True,
                                     url=meta['urls']['page'], params=meta['requests']['url'])['items'][0]

    jobs_dict = {}
    for i in response['requisitionList']:
        jobs_dict.update(jobs(i))

    return(jobs_dict)

#%%
# insert arbitrary number of jobs for initial get
meta['requests']['finder'], meta['requests']['url'] = update_nojobs(100,
                                                                    meta['requests']['finder'],
                                                                    meta['requests']['url'])

if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)