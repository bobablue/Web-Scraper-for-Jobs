import os
import datetime
from bs4 import BeautifulSoup

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':20, # default, cannot be changed

        'requests':{'url':{'location':['Singapore'], 'page':1}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(soup_obj):
    data = soup_obj.find_all('div', class_='sMn82b')
    data_dict = {}
    for i in data:
        url = meta['urls']['job'] + i.find('a', class_='WpHeLc VfPpkd-mRLv6 VfPpkd-RLmnJb')['href']
        data_dict[url] = {'Title':i.find('h3', class_='QJPWVe').text,
                          'Location':i.find('span', class_='pwO9Dc vo5qdf').text.replace('place','')}

    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'])
    bs_obj = BeautifulSoup(response.content, 'html.parser')

    num_jobs = int(bs_obj.find('span', class_='SWhIm').text)
    pagesize = meta['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(bs_obj) # parse first page

    # compile subsequent pages
    for i in range(2, pages+1):
        meta['requests']['url']['page'] = i
        response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'])
        bs_obj = BeautifulSoup(response.content, 'html.parser')
        jobs_dict.update(jobs(bs_obj))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)