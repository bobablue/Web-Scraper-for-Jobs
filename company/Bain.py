import os
import datetime
from bs4 import BeautifulSoup
import re

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':10, # default, unable to changes
        'chars':'[]',

        'requests':{'url':{'4783':'[22013051]', 'folderOffset':0}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(soup_obj):
    data = soup_obj.find_all('div', class_='article__header__text')
    data_dict = {}
    for i in data:
        data_dict[i.find('a')['href']] = {'Title':i.find('a').text.strip(),
                                          'Location':i.find('div', class_='article__header__text__subtitle').text.strip()}
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'],
                                 params=scrape_funcs.encode(meta['requests']['url'], meta['chars']))

    bs_obj = BeautifulSoup(response.content, 'html.parser')

    if 'no jobs found' in bs_obj.text.lower():
        return({})

    num_jobs = ' '.join(bs_obj.find('div', class_='list-controls__text__legend').text.split())
    num_jobs = int(re.search(r'(\d+) result', num_jobs).group(1))
    pagesize = meta['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(bs_obj) # parse fist page
    for i in range(1,pages):
        meta['requests']['url']['folderOffset'] = pagesize * i
        response = scrape_funcs.pull('get', url=meta['urls']['page'],
                                     params=scrape_funcs.encode(meta['requests']['url'], meta['chars']))

        bs_obj = BeautifulSoup(response.content, 'html.parser')
        jobs_dict.update(jobs(bs_obj))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)