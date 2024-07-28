# data is embedded in html script tag. find source, instead of having to load the html then parse the string.
import os
import datetime
from bs4 import BeautifulSoup
import json

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'locations':['singapore'],

        'requests':{'headers':{'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) Gecko/20100101 Firefox/128.0',
                               'Accept-Language':'en-US,en;q=0.5',
                               'Priority':'u=0, i'}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        locations = ' | '.join(sorted([x['name'].replace(' - Remote','') for x in i['locations']]))
        data_dict[meta['urls']['job']+i['id']] = {'Title':i['text'],
                                                  'Job Function':i['team'],
                                                  'Location':locations}

    data_dict = scrape_funcs.restrict_loc(data_dict, meta['locations'])
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    # get all jobs, then filter
    response = scrape_funcs.pull('get', url=meta['urls']['page'], headers=meta['requests']['headers'])
    bs_obj = BeautifulSoup(response.content, 'html.parser')

    json_obj = bs_obj.find('script', id='__NEXT_DATA__').text
    json_obj = json_obj.split('"positions":')[-1] # after this substring
    json_obj = json_obj.split(',"isLanding":')[0] # before this substring
    json_obj = json.loads(json_obj)

    jobs_dict = jobs(json_obj)
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)