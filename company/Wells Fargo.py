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

        # 50 is max page size
        'requests':{'url':{'country':['Singapore'], 'pagesize':50, 'page':1},
                    'headers':{'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0'}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(bs_obj):
    data = bs_obj.find_all('div', class_='card-body')

    urls = [i.find('a', class_='stretched-link')['href'] for i in data]
    titles = [i.find('a').text.strip() for i in data]

    job_meta = [i.find_all('li', class_='list-inline-item') for i in data]
    locs = [i[0].text.strip() for i in job_meta]
    job_funcs = [i[1].text.strip() for i in job_meta]

    data_zip = zip(urls, titles, locs, job_funcs)

    data_dict = {}
    for i in data_zip:
        data_dict[meta['urls']['job']+i[0]] = {'Title':i[1], 'Location':i[2], 'Job Function':i[3]}

    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    # get total number of jobs and pages to loop through and parse first page of results
    response = scrape_funcs.pull('get', url=meta['urls']['page'],
                                 params=meta['requests']['url'], headers=meta['requests']['headers'])

    bs_obj = BeautifulSoup(response.content, 'html.parser')

    num_jobs = int(re.findall(r'(\d+) matching jobs', bs_obj.find('p', class_='job-count').text)[0])
    pages = num_jobs//meta['requests']['url']['pagesize'] + (num_jobs % meta['requests']['url']['pagesize']>0)

    jobs_dict = {}
    jobs_dict.update(jobs(bs_obj))

    # loop through pages
    for pg in range(2, pages+1):
        meta['requests']['url']['page'] = pg
        response = scrape_funcs.pull('get', url=meta['urls']['page'],
                                     params=meta['requests']['url'], headers=meta['requests']['headers'])

        bs_obj = BeautifulSoup(response.content, 'html.parser')
        jobs_dict.update(jobs(bs_obj))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)