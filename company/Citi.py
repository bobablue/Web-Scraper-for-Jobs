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
    try:
        data_dict = {meta['urls']['job']+soup_obj.find('a')['href']: {'Title':soup_obj.find('h2').text,
                                                                      'Location':soup_obj.find('span', class_='job-location').text}}

    # repeated 'a' html tag: 1st contains job data, 2nd is just "learn more" with no data
    except (AttributeError, TypeError):
        return(dict())

    # clean up location string
    for i,j in data_dict.items():
        loc = ''.join(j['Location'].split())
        loc = loc.split(',')
        loc = set(i.lower() for i in loc)
        if loc=={'singapore'}:
            j['Location'] = 'Singapore'

    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', json_decode=True, url=meta['urls']['page'],
                                 params=scrape_funcs.encode(meta['requests']['url'], meta['chars']))

    # if no_jobs>default in RecordsPerPage, update meta['requests']['url'] and call again with updated number
    no_jobs = int(BeautifulSoup(response['results'], 'html.parser').find('section')['data-total-results'])
    if no_jobs>meta['requests']['url']['RecordsPerPage']:
        meta['requests']['url']['RecordsPerPage'] = no_jobs
        response = scrape_funcs.pull('get', json_decode=True, url=meta['urls']['page'],
                                     params=scrape_funcs.encode(meta['requests']['url'], meta['chars']))

    bs_obj = BeautifulSoup(response['results'], 'html.parser').find(id='search-results-list')
    jobs_dict = {}
    for i in bs_obj.find_all('li', class_=False):
        jobs_dict.update(jobs(i))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)