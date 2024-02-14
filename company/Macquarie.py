import os
import datetime
from bs4 import BeautifulSoup

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'url':{'location':['singapore'], 'page-items':1000}}}

#%% functions
#%% parse beautifulsoup object into dict
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(soup_obj):
    data = soup_obj.find_all('div', class_='pu_resultslist')

    url_titles = [i.find('a', class_='job-link') for i in data[0].find_all('div', class_='col-sm-7')]
    urls = [i['href'] for i in url_titles]
    titles = [i.text.strip() for i in url_titles]

    locs = [i.find_all('span', class_='location') for i in data]
    locs = [i for j in locs for i in j]
    locs = [i.text for i in locs]

    data_zip = zip(urls, titles, locs)

    data_dict = {}
    for i in data_zip:
        data_dict[meta['urls']['job']+i[0]] = {'Title':i[1], 'Location':i[2]}

    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], params=meta['requests']['url'])
    bs_text = BeautifulSoup(response.content, 'html.parser')
    jobs_dict = jobs(bs_text)
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)