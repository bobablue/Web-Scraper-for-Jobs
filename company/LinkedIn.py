import os
import datetime
from bs4 import BeautifulSoup
import time

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':25,

        'requests':{'headers':{'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0',
                               'Accept':'*/*',
                               'Accept-Language':'en-US,en;q=0.5',
                               'Accept-Encoding':'gzip, deflate, br'},

                    'url':{'f_C':'1337', 'location':'Singapore',
                           'position':1, 'pageNum':0, 'start':0}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(soup_obj):
    soup_obj = soup_obj.find_all('ul', class_='jobs-search__results-list')
    data_dict = {}
    for i in soup_obj:
        job = i.find_all('li')

        for j in job:
            url = j.find('a')['href']
            title = ' '.join(j.find('a').text.split())
            company = ' ' .join(j.find('h4').text.split())
            location = [' '.join(x.text.split()) for x in j.find_all('span', class_='job-search-card__location')][0]

            if company.lower()=='linkedin':
                data_dict[url] = {'Title':title, 'Location':location}

    data_dict = scrape_funcs.clean_loc(data_dict)
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():

    # prone to 429 errors, so try 3 times
    attempt = 1
    while attempt<=3:

        response = scrape_funcs.pull('get', url=meta['urls']['page'],
                                     headers=meta['requests']['headers'], params=meta['requests']['url'])

        if response.status_code==429:
            time.sleep(3)
            attempt = attempt+1

        elif response.status_code==200:
            break

    if response.status_code==429:
        return({})

    bs_obj = BeautifulSoup(response.content, 'html.parser')

    num_jobs = int([i.text for i in bs_obj.find_all('span', class_='results-context-header__job-count')][0])
    pagesize = meta['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(bs_obj) # parse first page

    # compile subsequent pages
    for i in range(1,pages):
        meta['requests']['url']['start'] = i * pagesize
        response = scrape_funcs.pull('get', url=meta['urls']['page'],
                                     headers=meta['requests']['headers'], params=meta['requests']['url'])

        bs_obj = BeautifulSoup(response.content, 'html.parser')
        jobs_dict.update(jobs(bs_obj))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)