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

        'requests':{'url':{'locationsearch':'singapore', 'startrow':0}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(soup_obj):
    data = soup_obj.find_all('span', class_='jobTitle hidden-phone')
    links = [i.find('a', class_='jobTitle-link')['href'] for i in data]
    titles = [i.text.strip() for i in data]
    locs = [i.text.strip() for i in soup_obj.find_all('td', class_='colLocation hidden-phone')]

    data = zip(links, titles, locs)
    data_dict = {}

    for i in data:
        data_dict[meta['urls']['job'] + i[0]] = {'Title':i[1], 'Location':i[2]}

    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'])
    bs_obj = BeautifulSoup(response.content, 'html.parser')

    num_jobs = bs_obj.find('span', class_='paginationLabel').text.strip()
    num_jobs = int(re.search(r'of (\d+)', num_jobs).group(1))
    pagesize = meta['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(bs_obj) # parse first page

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