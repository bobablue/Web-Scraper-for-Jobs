import os
import datetime
from bs4 import BeautifulSoup
import re

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        # 50 records per page is hard limit
        'requests':{'url':{'1017':'[67209]', '1017_format':812,
                           'listFilterMode':1,
                           'pipelineRecordsPerPage':50, 'pipelineOffset':0}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(soup_obj):

    # extract data fields in list type from response object
    meta = [' '.join(i.text.split()) for i in soup_obj.find_all('span', class_='article--item')]
    urls = [i['href'] for i in soup_obj.select('h3 a')][:-2]
    titles = [' '.join(i.text.split()) for i in soup_obj.select('h3 a')][:-2]
    jobfunc = meta[1::5]
    location = meta[0::5]

    # combine all lists of data fields into dictionary
    data = zip(urls, titles, location, jobfunc)
    data_dict = {}
    for d in data:
        data_dict[d[0]] = {'Title':d[1], 'Location':d[2], 'Job Function':d[3]}

    data_dict = scrape_funcs.clean_loc(data_dict)
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    # get total number of jobs and determine number of pages of career website
    response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'])
    bs_obj = BeautifulSoup(response.content, 'html.parser')

    num_jobs = ' '.join(bs_obj.find_all('div', class_='list-controls__text__legend')[0].text.split())
    num_jobs = int(re.compile(r'(\d*)\+? results').findall(num_jobs)[0])
    pages = num_jobs//meta['requests']['url']['pipelineRecordsPerPage'] + (num_jobs % meta['requests']['url']['pipelineRecordsPerPage']>0)

    # parse first page
    jobs_dict = {}
    jobs_dict.update(jobs(bs_obj))

    # compile jobs from all pages after first, into main dict (update meta['requests']['url'] pipelineOffset)
    for pg in range(pages-1):
        meta['requests']['url']['pipelineOffset'] = (pg+1) * meta['requests']['url']['pipelineRecordsPerPage']
        response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'])
        bs_obj = BeautifulSoup(response.content, 'html.parser')
        jobs_dict.update(jobs(bs_obj))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)