import os
import datetime
import requests
from bs4 import BeautifulSoup
import re

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'locations':['singapore'],
        'job_max':50, # default, unable to change

        # not sure what the country code for singapore is, as there are no current vacancies. add when available.
        'requests':{'post':{'__VIEWSTATE':None,
                            '__VIEWSTATEGENERATOR':None,
                            '__EVENTVALIDATION':None,
                            'ctl00$ctl00$moteurRapideOffre$ctl01$OfferCriteria$Location$GeographicalAreaCollection':'',
                            'ctl00$ctl00$moteurRapideOffre$BT_recherche':'Start+search'},

                    'url':{'page':1}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(bs_obj):
    urls = [meta['urls']['job']+i['href'] for i in bs_obj.find_all('a', class_='ts-offer-list-item__title-link')]
    titles = [i.text.strip() for i in bs_obj.find_all('a', class_='ts-offer-list-item__title-link')]

    # string structure: employment type | department | country | city
    job_info = [i.find_all('li') for i in bs_obj.find_all('ul', class_='ts-offer-list-item__description')]
    job_info = [[x.text.strip() for x in i] for i in job_info]

    locs = [i[-2:] for i in job_info]
    locs = [[x for x in i if x!=''] for i in locs] # some posts don't have the last/4th element (city)
    locs = [' | '.join(i) for i in locs]

    job_func = [i[1] for i in job_info]

    data = zip(urls, titles, locs, job_func)

    data_dict = {}
    for d in data:
        data_dict[d[0]] = {'Title':d[1], 'Location':d[2], 'Job Function':d[3]}

    # restrict to singapore only
    data_dict = {k:v for k,v in data_dict.items() if v['Location'].lower() in meta['locations']}
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    # get cookie, and tokens to generate post_data
    response = scrape_funcs.pull('post', url=meta['urls']['cookie'])
    cookie = response.cookies.get_dict()

    bs_obj = BeautifulSoup(response.content, 'html.parser')
    for k,v in meta['requests']['post'].items():
        if v is None:
            meta['requests']['post'][k] = bs_obj.find(id=k)['value']

    # create session object
    session = requests.Session()
    session.post(url=meta['urls']['cookie'], cookies=cookie, data=meta['requests']['post'])

    # get first page and get number of jobs
    response = session.get(url=meta['urls']['page'], cookies=cookie, params=meta['requests']['url'])
    bs_obj = BeautifulSoup(response.content, 'html.parser')

    num_jobs = bs_obj.find('span', id='ctl00_ctl00_corpsRoot_corps_Pagination_TotalOffers').text
    num_jobs = int(re.search(r'(\d+)', num_jobs).group(0))
    pagesize = meta['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(bs_obj) # parse first page

    # compile subsequent pages
    for i in range(2, pages+1):
        meta['requests']['url']['page'] = i
        response = session.get(url=meta['urls']['page'], cookies=cookie, params=meta['requests']['url'])
        bs_obj = BeautifulSoup(response.content, 'html.parser')
        jobs_dict.update(jobs(bs_obj))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)