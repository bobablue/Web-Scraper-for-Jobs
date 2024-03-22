import os
import datetime
from bs4 import BeautifulSoup

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'headers':{'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0'}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(soup_obj):
    soup_obj = soup_obj.find_all('div', class_='fl-post-feed')
    data_dict = {}
    for i in soup_obj:

        titles_urls = [x.find('a') for x in i]
        titles = [x.text for x in titles_urls if not isinstance(x,int)]
        urls = [x['href'] for x in titles_urls if not isinstance(x,int)]
        locs = [x.text for x in i.find_all('div', class_='fl-post-info')]

        data = zip(urls, titles, locs)
        for j in data:
            data_dict[j[0]] = {'Title':j[1], 'Location':j[2]}

    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], headers=meta['requests']['headers'])
    bs_obj = BeautifulSoup(response.content, 'html.parser')
    jobs_dict = jobs(bs_obj) # not sure how the structure would change if there are more than N jobs
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)