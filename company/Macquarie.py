import os
import datetime
from bs4 import BeautifulSoup

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'url':{'592':'[887500]',
                           'jobOffset':0,
                           'jobRecordsPerPage':9}}} # unable to change records per page

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(soup_obj):
    data_dict = {}
    data = soup_obj.find_all('div', class_='article__container')
    for i in data:
        url_title = i.find('a', class_='link')
        loc = i.find('span', class_='list-item-location').text

        # tuple of (location, date posted, job function). if job func not present, insert blank at last element
        job_func = i.find_all('div', class_='article__details__data')
        job_func = [i.text.strip() for i in job_func]
        job_func = job_func[2] if len(job_func)==3 else ''

        data_dict[url_title['href']] = {'Title':url_title.text.strip(), 'Job Function':job_func, 'Location':loc}

    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'])
    bs_obj = BeautifulSoup(response.content, 'html.parser')

    num_jobs = int(bs_obj.find('span', class_='section__header--top--result').text)
    pagesize = meta['requests']['url']['jobRecordsPerPage']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(bs_obj) # parse first page

    # compile subsequent pages
    page_info = scrape_funcs.gen_page_info(params=meta['requests']['url'],
                                           page_range=range(1, pages+1),
                                           page_param='jobOffset',
                                           multiplier=pagesize)

    responses = scrape_funcs.concurrent_pull('get', url=meta['urls']['page'], params=page_info)

    for v in responses.values():
        jobs_dict.update(jobs(BeautifulSoup(v.content, 'html.parser')))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)