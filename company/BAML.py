import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'url':{'country':'Singapore', 'rows':100, 'search':'jobsByCountry'}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        data_dict[meta['urls']['job']+i['jcrURL']] = {'Title':i['postingTitle'],
                                                      'Job Function':i['family'],
                                                      'Location':i['location']}
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', json_decode=True, url=meta['urls']['page'], params=meta['requests']['url'])
    no_jobs = response['totalMatches']

    # if no_jobs>default in rows, update url_params and call again with updated number
    if no_jobs>meta['requests']['url']['rows']:
        meta['requests']['url']['rows'] = no_jobs
        response = scrape_funcs.pull('get', json_decode=True, url=meta['urls']['page'], params=meta['requests']['url'])

    jobs_dict = jobs(response['jobsList'])
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)