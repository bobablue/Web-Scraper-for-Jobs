import os
import datetime
from bs4 import BeautifulSoup

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'url':{'keywords':'green link digital bank', 'location':'singapore',
                           'position':1, 'pageNum':0, 'start':0}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(soup_obj):
    soup_obj = soup_obj.find('ul', class_='jobs-search__results-list')
    data_dict = {}
    for job in soup_obj.find_all('li'):

        # some jobs are not from company itself; only add to dict if company name is relevant
        if os.path.splitext(os.path.basename(__file__))[0].lower() in job.find('h4', class_='base-search-card__subtitle').text.lower():
            title = job.find('a')
            url = title['href'].split('?')[0] # seems to have duplicate posts with diff URL params
            data_dict[url] = {'Title':' '.join(title.text.strip().split()),
                              'Location':job.find('span', class_='job-search-card__location').text.strip()}

    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'])
    bs_obj = BeautifulSoup(response.content, 'html.parser')
    jobs_dict = jobs(bs_obj) # parse first page

    num_jobs = int([i.text for i in bs_obj.find_all('span', class_='results-context-header__job-count')][0])
    pagesize = len(jobs_dict) # assume that first request is the pagesize, could be dynamic
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    # compile subsequent pages
    page_info = scrape_funcs.gen_page_info(params=meta['requests']['url'],
                                           page_range=range(1, pages),
                                           page_param='start',
                                           multiplier=pagesize)

    responses = scrape_funcs.concurrent_pull('get', url=meta['urls']['page'], params=page_info)

    for v in responses.values():
        jobs_dict.update(jobs(BeautifulSoup(v.content, 'html.parser')))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)