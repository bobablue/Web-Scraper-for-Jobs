import os
import datetime
from bs4 import BeautifulSoup
import re

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0])}
meta['urls']['page'] = meta['urls']['page'].replace('/?','/?location=singapore&') # narrow search to singapore only

#%% functions
#%% parse beautifulsoup object into dict
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def extract_data(soup_obj):
    data = soup_obj.find_all('tr', class_='data-row')
    data_dict = {}
    for no, i in enumerate(data):
        job = i.find('a', class_='jobTitle-link')
        data_dict[f"{meta['urls']['job']}{job['href']}"] = {'Title':job.text,
                                                            'Job Function':i.find('span', class_='jobDepartment').text,
                                                            'Location':i.find('span', class_='jobLocation').text.strip()}
    return(data_dict)

#%% get total number of pages of career website and generate list of URLs for each page
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'])
    bs_text = BeautifulSoup(response.content, 'html.parser').find('caption').text
    results_per_pg = int(re.compile(r'Results \d+ to (\d+)').findall(bs_text)[0])
    pages = int(re.compile(r'Page \d+ of (\d+)').findall(bs_text)[0])
    pages = [f"{meta['urls']['page']}{i*results_per_pg}" for i in range(pages)]

    # compile jobs from all pages into 1 dict
    jobs_dict = {}
    for pg in pages:
        response = scrape_funcs.pull('get', url=pg)
        bs_obj = BeautifulSoup(response.content, 'html.parser')
        jobs_dict.update(extract_data(bs_obj))
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    #scrape_funcs.to_json(meta['urls']['company'], jobs_dict)