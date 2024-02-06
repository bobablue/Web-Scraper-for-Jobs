import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'job_max':1000,
                    'json':{'lang':'en', 'tax_country':'singapore-en', 'from':0}}}

meta['requests']['json']['size'] = meta['requests']['job_max']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(data):
    data_dict = {}
    for i in data:
        data_dict[meta['urls']['job']+i['link']['url']] = {'Title':scrape_funcs.decode(i['title']),
                                                           'Job Function':i['sector'],
                                                           'Location':i['country']}
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('post', url=meta['urls']['page'], json=meta['requests']['json'], json_decode=True)

    # assume num_jobs would not be >1,000, but check just in case
    num_jobs = response['data']['total']
    if num_jobs>meta['requests']['job_max']:
        raise ValueError(f"Number of posted jobs greater than defined max: {num_jobs}\nCheck how to pull all")

    jobs_dict = jobs(response['data']['items'])
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)