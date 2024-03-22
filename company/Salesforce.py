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
        'job_max':1000,

        'requests':{'headers':{'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0'},

                    'url':{'country':'Singapore', 'page':1}}}

meta['requests']['url']['pagesize'] = meta['job_max']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(soup_obj):
    data = soup_obj.find_all('div', class_='card card-job')
    data_dict = {}
    for i in data:
        job = i.find('a', class_='stretched-link js-view-job')
        data_dict[meta['urls']['job'] + job['href']] = {'Title':job.text,
                                                        'Job Function':i.find('p', class_='card-subtitle').text,
                                                        'Location':' '.join(i.find('li', class_='list-inline-item').text.split())}

    data_dict = scrape_funcs.clean_loc(data_dict)
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'],
                                 headers=meta['requests']['headers'], params=meta['requests']['url'])

    bs_obj = BeautifulSoup(response.content, 'html.parser')

    num_jobs = bs_obj.find('p', class_='job-count').text
    num_jobs = int(re.search(r'of (\d+) matching', num_jobs).group(1))
    pagesize = meta['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(bs_obj) # parse first page

    # compile subsequent pages
    for i in range(2,pages+1):
        meta['requests']['url']['page'] = i
        response = scrape_funcs.pull('get', url=meta['urls']['page'],
                                     headers=meta['requests']['headers'], params=meta['requests']['url'])

        bs_obj = BeautifulSoup(response.content, 'html.parser')
        jobs_dict.update(jobs(bs_obj))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)