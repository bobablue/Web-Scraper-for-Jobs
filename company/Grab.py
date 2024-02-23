import os
import datetime
from bs4 import BeautifulSoup

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'locations':['Singapore, SG'],

        'requests':{'url':{'type':'location', 'value':None, 'page':0}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(soup_obj):
    data = soup_obj.find_all('a', class_='link--block details')
    data_dict = {}
    for i in data:
        data_dict[i['href']] = {'Title':i.find('h4').text, 'Location':meta['requests']['url']['value']}
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    jobs_dict = {}

    # loop by loc as html does not contain loc info without loading entire job portal page
    for loc in meta['locations']:
        meta['requests']['url']['value'] = loc
        response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'])

        bs_obj = BeautifulSoup(response.content, 'html.parser')
        jobs_dict.update(jobs(bs_obj)) # parse first page

        # no way to get number of jobs without loading entire job portal page
        # so, loop until length of jobs_dict does not change (10 per pull, unable to change)
        # set 'new' greater than 'old' for first iteration so that while loop doesn't break on first loop
        num_jobs = {'old':len(jobs_dict), 'new':len(jobs_dict)+1}
        while num_jobs['new']>num_jobs['old']:
            num_jobs['old'] = len(jobs_dict)
            meta['requests']['url']['page'] = meta['requests']['url']['page'] + 1

            response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'])
            bs_obj = BeautifulSoup(response.content, 'html.parser')

            jobs_dict.update(jobs(bs_obj))
            num_jobs['new'] = len(jobs_dict)

        # reset params after pulling for each country
        meta['requests']['url']['page'] = 0
        meta['requests']['url']['value'] = None

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)