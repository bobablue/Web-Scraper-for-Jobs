import os
import datetime
import re
from bs4 import BeautifulSoup

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'chars':'+-[]',

        'requests':{'url':{'RecordsPerPage':100,
                           'SearchResultsModuleName':'Search+Results',
                           'FacetFilters[0].ID':'1880251',
                           'FacetFilters[0].FacetType':2,
                           'FacetFilters[0].IsApplied':'true'}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(bs_obj):
    data_dict = {}
    for i in bs_obj.find_all('div', class_='list-item list-item--card fs-column fs-top round-corners bg--pale-blue-light p-1 text--black'):
        job_title = i.find('a', class_='headline-3 job-title--link text--black')
        data_dict[meta['urls']['job']+job_title['href']] = {'Title':job_title.text,
                                                            'Location':i.find('div', class_='job-location').text}

    data_dict = scrape_funcs.clean_loc(data_dict)
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'],
                                 params=scrape_funcs.encode(meta['requests']['url'], meta['chars']))

    num_jobs = int(re.compile(r'data-total-results="(\d+)"').findall(response.json()['results'])[0])

    # if num_jobs>default in RecordsPerPage, update url_params and call again with updated number
    if num_jobs>meta['requests']['url']['RecordsPerPage']:
        meta['requests']['url']['RecordsPerPage'] = num_jobs
        response = scrape_funcs.pull('get', url=meta['urls']['page'],
                                     params=scrape_funcs.encode(meta['requests']['url'], meta['chars']))

    bs_obj = BeautifulSoup(response.json()['results'], 'html.parser')
    jobs_dict = jobs(bs_obj)

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)