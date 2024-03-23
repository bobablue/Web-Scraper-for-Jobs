import os
import datetime
from bs4 import BeautifulSoup

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'chars':'%+',

        'requests':{'url':{'RecordsPerPage':100,
                           'FacetFilters%5B0%5D.ID':1880251, # singapore
                           'FacetFilters%5B0%5D.FacetType':2,
                           'FacetFilters%5B0%5D.IsApplied':'true',
                           'SearchResultsModuleName':'Search+Results'}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(soup_obj):
    data_dict = {}
    soup_obj = soup_obj.find(id='search-results-list')
    for i in soup_obj.find_all('li', class_=False):
        try:
            data_dict[meta['urls']['job']+i.find('a')['href']] = {'Title':i.find('h2').text,
                                                                  'Location':i.find('span', class_='job-location').text}

        # repeated 'a' html tag: 1st contains job data, 2nd is just "learn more" with no data
        except (AttributeError, TypeError):
            pass

    data_dict = scrape_funcs.clean_loc(data_dict)
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', json_decode=True, url=meta['urls']['page'],
                                 params=scrape_funcs.encode(meta['requests']['url'], meta['chars']))

    # if num_jobs>default in RecordsPerPage, update meta['requests']['url'] and call again with updated number
    num_jobs = int(BeautifulSoup(response['results'], 'html.parser').find('section')['data-total-results'])
    if num_jobs>meta['requests']['url']['RecordsPerPage']:
        meta['requests']['url']['RecordsPerPage'] = num_jobs
        response = scrape_funcs.pull('get', json_decode=True, url=meta['urls']['page'],
                                     params=scrape_funcs.encode(meta['requests']['url'], meta['chars']))

    bs_obj = BeautifulSoup(response['results'], 'html.parser')
    jobs_dict = jobs(bs_obj)
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)