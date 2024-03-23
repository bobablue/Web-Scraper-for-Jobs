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
        'job_max':25,

        'requests':{'url':{'locationsearch':'Singapore', 'startrow':0}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(soup_obj):
    soup_obj = soup_obj.find_all('ul', id='job-tile-list')
    data_dict = {}
    for i in soup_obj:
        jobs = i.find_all('a', class_='jobTitle-link fontcolor632603bfd7cc812e')
        urls = [meta['urls']['job'] + i['href'] for i in jobs]
        titles = [' '.join(x.text.split()) for x in jobs]

        job_funcs = i.find_all('div', class_='section-field customfield2 fontcolora014d7df0fa8445f')
        job_funcs = [' '.join(x.text.split()).strip('Unit ') for x in job_funcs]

        locs = i.find_all('div', class_='section-field location fontcolora014d7df0fa8445f')
        locs = [' '.join(x.text.split()).strip('Location ') for x in locs]

        data = zip(urls, titles, job_funcs, locs)
        for j in data:
            data_dict[j[0]] = {'Title':j[1], 'Job Function':j[2], 'Location':j[3]}

    data_dict = scrape_funcs.clean_loc(data_dict)
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'])
    bs_obj = BeautifulSoup(response.content, 'html.parser')

    num_jobs = bs_obj.find('span', id='tile-search-results-label').text
    num_jobs = int(re.search(r'\((\d+)\)', num_jobs).group(1))
    pagesize = meta['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(bs_obj) # parse first page

    # compile subsequent pages
    for i in range(1,pages):
        meta['requests']['url']['startrow'] = i * pagesize
        response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'])
        bs_obj = BeautifulSoup(response.content, 'html.parser')
        jobs_dict.update(jobs(bs_obj))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)