import os
import datetime
import xml.etree.ElementTree as et

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0])}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(response_obj):
    xml_obj = et.fromstring(response_obj.text)
    jobs = xml_obj.find('jobs')

    data_dict = {}
    for job in jobs:
        data_dict[job.find('url').text] = {'Title':job.find('title').text,
                                           'Location':job.find('location').text,
                                           'Job Function':job.find('adcode').text}

    data_dict = scrape_funcs.clean_loc(data_dict)
    data_dict = {k:v for k,v in data_dict.items() if v['Location'].lower()=='singapore'}
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'])
    jobs_dict = jobs(response)
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)