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
        'job_max':20, # default, unable to change

        'requests':{'url':{'location':'singapore-SGP', 'page':1}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(soup_obj):
    titles_funcs = soup_obj.find_all('td', class_='table-col-1')
    links = [i.find('a')['href'] for i in titles_funcs]
    titles = [i.find('a').text for i in titles_funcs]
    job_funcs = [i.find('span', class_='table--advanced-search__role').text for i in titles_funcs]

    locs = soup_obj.find_all('td', class_='table-col-2')
    locs = [' '.join(i.text.split()) for i in locs]

    data = zip(links, titles, job_funcs, locs)
    data_dict = {}
    for i in data:
        data_dict[meta['urls']['job'] + i[0]] = {'Title':i[1], 'Job Function':i[2], 'Location':i[3]}

    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'])
    bs_obj = BeautifulSoup(response.content, 'html.parser')

    num_jobs = bs_obj.find('h2', id='resultCount').find('span').text
    num_jobs = int(re.search(r'(\d+) Result\(s\)', num_jobs).group(1))
    pagesize = meta['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(bs_obj) # parse first page

    # compile subsequent pages
    for i in range(2, pages+1):
        meta['requests']['url']['page'] = i
        response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'])
        bs_obj = BeautifulSoup(response.content, 'html.parser')
        jobs_dict.update(jobs(bs_obj))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)