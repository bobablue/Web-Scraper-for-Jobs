import os
import datetime
from bs4 import BeautifulSoup

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'locations':['singapore'],

        'requests':{'headers':{'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) Gecko/20100101 Firefox/128.0'}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(bs_obj):
    bs_obj = bs_obj.find('ul', id='careers_list')
    bs_obj = bs_obj.find_all('li')
    data_dict = {}
    for i in bs_obj:
        url = meta['urls']['job'] + i.find('a')['href'].replace(r'.','')
        data_dict[url] = {'Title':i.find('h4').text,
                          'Job Function':' '.join(i['data-department'].split('-')).title(),
                          'Location':' | '.join(sorted(i['data-location'].replace('-',' ').title().split('|')))}

    # restrict to selected locations
    data_dict = scrape_funcs.restrict_loc(data_dict, meta['locations'])
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], headers=meta['requests']['headers'])
    jobs_dict = jobs(BeautifulSoup(response.content, 'html.parser'))
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)