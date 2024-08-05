import os
import datetime
from bs4 import BeautifulSoup

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'locations':['singapore'],
        'job_max':20,

        # not sure what the country code for singapore is, as there are no current vacancies. add when available.
        'requests':{'url':{'page':1, 'resultsPerPage':None}}}

meta['requests']['url']['resultsPerPage'] = meta['job_max']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(bs_obj):
    data_dict = {}

    data = bs_obj.find('tbody')
    data = data.find_all('tr')
    for i in data:
        url_title = i.find('a')
        title = url_title['title']
        url = url_title['href']
        loc = i.find('td', label='Location').text.strip()
        data_dict[meta['urls']['job'] + url] = {'Title':title, 'Location':loc}

    data_dict = scrape_funcs.restrict_loc(data_dict, meta['locations'])
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'])
    bs_obj = BeautifulSoup(response.content, 'html.parser')

    num_jobs = int(bs_obj.find('span', attrs={'data-js':'jobs-table-counter'}).text)
    pagesize = meta['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(bs_obj) # parse first page

    # compile subsequent pages
    page_info = scrape_funcs.gen_page_info(params=meta['requests']['url'],
                                           page_range=range(2, pages+1),
                                           page_param='page',
                                           multiplier=1)

    responses = scrape_funcs.concurrent_pull('get', url=meta['urls']['page'], params=page_info)

    for v in responses.values():
        jobs_dict.update(jobs(BeautifulSoup(v.content, 'html.parser')))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)