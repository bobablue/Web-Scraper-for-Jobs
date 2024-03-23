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
        'job_max':500,

        'requests':{'headers':{'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0'},

                    'url':{'options':[320], 'page':1}}}

meta['requests']['url']['size'] = meta['job_max']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(bs_obj):
    titles = bs_obj.find_all('a', class_='attrax-vacancy-tile__title attrax-vacancy-tile__item attrax-button')
    links = [i['href'] for i in titles]
    titles = [i.text.strip() for i in titles]

    job_funcs = bs_obj.find_all('div', class_='attrax-vacancy-tile__option-team-valueset attrax-vacancy-tile__item-valueset')
    job_funcs = [i.find('p', class_='attrax-vacancy-tile__item-value').text.strip() for i in job_funcs]

    locs = bs_obj.find_all('div', class_='attrax-vacancy-tile__location-freetext attrax-vacancy-tile__item')
    locs = [i.find('p', class_='attrax-vacancy-tile__item-value').text.strip() for i in locs]

    data = zip(links, titles, job_funcs, locs)
    data_dict = {}
    for i in data:
        data_dict[meta['urls']['job'] + i[0]] = {'Title':i[1], 'Job Function':i[2], 'Location':i[3]}

    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'],
                                 headers=meta['requests']['headers'], params=meta['requests']['url'])

    bs_obj = BeautifulSoup(response.content, 'html.parser')

    num_jobs = bs_obj.find('span', class_='attrax-pagination__total-results').text.strip()
    num_jobs = int(re.search(r'(\d+) results', num_jobs).group(1))
    pagesize = meta['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(bs_obj) # parse first page

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