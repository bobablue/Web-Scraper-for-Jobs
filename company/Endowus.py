import os
import datetime
from bs4 import BeautifulSoup

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'locations':['singapore']}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(soup_obj):
    soup_obj = soup_obj.find_all('div', class_='job-postings-collection-list__item w-dyn-item')
    data_dict = {}
    for i in soup_obj:
        job = i.find_all('a', class_='job-post-card__link w-inline-block')[0]
        url = meta['urls']['job'] + job['href']
        title = job.find('div', class_='job-posting-card__title-txt').text
        job_func, loc = job.find('div', class_='job-post-card__position').text.split(' | ')
        data_dict[url] = {'Title':title, 'Job Function':job_func, 'Location':loc}

    data_dict = scrape_funcs.restrict_loc(data_dict, meta['locations'])
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'])
    jobs_dict = jobs(BeautifulSoup(response.content, 'html.parser'))
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)