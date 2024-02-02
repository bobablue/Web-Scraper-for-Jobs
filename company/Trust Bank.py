import os
import datetime
from bs4 import BeautifulSoup

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0])}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(bs_obj):
    data_dict = {}
    for section in bs_obj.find_all('section'):
        dept = section.find('h3').text
        for job,location in zip(section.find_all('a'), section.find_all('span')):
            data_dict[f"{meta['urls']['job']}{job['href']}"] = {'Title':job.text,
                                                                'Job Function':dept,
                                                                'Location':location.text}
    return(data_dict)

#%% get all jobs (not sure how the loop/next page structure is like)
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'])
    bs_obj = BeautifulSoup(response.content, 'html.parser')
    jobs_dict = jobs(bs_obj)
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)