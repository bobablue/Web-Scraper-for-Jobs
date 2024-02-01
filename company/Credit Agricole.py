import os
import datetime
import requests
from bs4 import BeautifulSoup

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'requests':{'post':{'__VIEWSTATE':None,
                            '__VIEWSTATEGENERATOR':None,
                            '__EVENTVALIDATION':None,
                            'ctl00$ctl00$moteurRapideOffre$ctl02$OfferCriteria$Location$GeographicalAreaCollection':'169',
                            'ctl00$ctl00$moteurRapideOffre$BT_recherche':'Start+search'}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(bs_obj):
    urls = [meta['urls']['job']+i['href'] for i in bs_obj.find_all('a', class_='ts-offer-card__title-link')]
    titles = [i.text.strip() for i in bs_obj.find_all('a', class_='ts-offer-card__title-link')]
    locs = [i.find_all('li')[1].text for i in bs_obj.find_all('ul', class_='ts-offer-card-content__list')]
    data = zip(urls, titles, locs)

    data_dict = {}
    for d in data:
        data_dict[d[0]] = {'Title':d[1], 'Location':d[2]}
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    # get cookie, and tokens to generate post_data
    response = scrape_funcs.pull('post', url=meta['urls']['cookie'])
    cookie = response.cookies.get_dict()

    bs_obj = BeautifulSoup(response.content, 'html.parser')
    for k,v in meta['requests']['post'].items():
        if v is None:
            meta['requests']['post'][k] = bs_obj.find(id=k)['value']

    # get all jobs
    session = requests.Session()
    session.post(url=meta['urls']['cookie'], cookies=cookie, data=meta['requests']['post'])
    response = session.get(url=meta['urls']['page'], cookies=cookie)
    bs_obj = BeautifulSoup(response.content, 'html.parser')
    jobs_dict = jobs(bs_obj)
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)