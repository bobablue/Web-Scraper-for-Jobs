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

        'requests':{'url':{'for':'kkr', 'b':'https://www.kkr.com/careers/career-opportunities'}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(bs_obj):
    bs_obj = bs_obj.find_all('section', class_='level-0')
    jobs_all = {}

    # sections split by job function
    for i in bs_obj:
        job_func = i.find('h3').text

        # don't want generic 'join our talent community'
        if all(x in job_func.lower() for x in ['join','community']):
            continue

        urls = []
        titles = []
        for j in i.find_all('a'):
            urls.append(j['href'])
            titles.append(j.text)

        locs = []
        for j in i.find_all('span', class_='location'):
            locs.append(j.text)

        data = zip(urls, titles, [job_func] * len(urls), locs)
        for j in data:
            jobs_all[j[0]] = {'Title':j[1], 'Job Function':j[2], 'Location':j[3]}

    # filter to only locations selected
    jobs_filtered = {k:v for k,v in jobs_all.items() if any(x in v['Location'].lower() for x in meta['locations'])}
    return(jobs_filtered)

#%% not sure how the loop/next page structure is like
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'])
    bs_obj = BeautifulSoup(response.content, 'html.parser')
    jobs_dict = jobs(bs_obj)
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)