import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':500,

        'requests':{'finder':{'siteNumber':'CX_1001', 'limit':None, 'locationId':'300000000289639'}, # singapore
                    'url':{'expand':'requisitionList.secondaryLocations,flexFieldsFacet.values', 'finder':None}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        data_dict[meta['urls']['job'] + i['Id']] = {'Title':i['Title'], 'Location':i['PrimaryLocation']}
    data_dict = scrape_funcs.clean_loc(data_dict)
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', json_decode=True,
                                 url=meta['urls']['page'], params=meta['requests']['url'])['items'][0]

    # if num_jobs>default in limit, update params and call again with updated number
    num_jobs = response['TotalJobsCount']
    if num_jobs>meta['requests']['finder']['limit']:
        meta['requests']['finder'], meta['requests']['url'] = scrape_funcs.update_num_jobs(num_jobs,
                                                                                           meta['requests']['finder'],
                                                                                           meta['requests']['url'])

        response = scrape_funcs.pull('get', json_decode=True,
                                     url=meta['urls']['page'], params=meta['requests']['url'])['items'][0]

    jobs_dict = jobs(response['requisitionList'])
    return(jobs_dict)

#%%
# insert arbitrary number of jobs for initial get
meta['requests']['finder'], meta['requests']['url'] = scrape_funcs.update_num_jobs(meta['job_max'],
                                                                                   meta['requests']['finder'],
                                                                                   meta['requests']['url'])

if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)