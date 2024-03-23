import os
import datetime
from bs4 import BeautifulSoup

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'url':{'location_level_1':'SG', 'start':0}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(bs_obj):
    data = bs_obj.find_all('div', class_='careers-search-result')
    data_dict = {}
    for d in data:
        data_dict[meta['urls']['job']+d.find('a')['href']] = {'Title':d.find('a').text,
                                                              'Location':d.find(class_='meta-information').text.split(' | ')[-2],
                                                              'Job Function':d.find(class_='meta-information').text.split(' | ')[1]}
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'])
    bs_obj = BeautifulSoup(response.content, 'html.parser')

    jobs_dict = jobs(bs_obj) # parse first page

    # pagesize calculated using number of jobs posted on first page, num_jobs can be <50 even if default is 50
    num_jobs = int(bs_obj.find_all('strong')[1].text)
    pagesize = len(jobs_dict)
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    # compile subsequent pages
    for i in range(1,pages):
        meta['requests']['url']['start'] = i * pagesize
        response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'])
        bs_obj = BeautifulSoup(response.content, 'html.parser')
        jobs_dict.update(jobs(bs_obj))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)