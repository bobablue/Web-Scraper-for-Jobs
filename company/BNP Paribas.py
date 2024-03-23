import os
import datetime
from bs4 import BeautifulSoup

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'headers':{'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0',
                               'Accept-Language':'en-US,en;q=0.5'},

                    'url':{'page':1}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(bs_obj):
    card_types = ['category-2', 'category-2 focus', 'category-28 focus', 'category-33']
    card_types = [f"card-custom card-offer {i}" for i in card_types]

    data = []
    for i in card_types:
        data.extend([x.find('a') for x in bs_obj.find_all('article', class_=i)])

    urls = [i['href'] for i in data]
    titles = [i.find('h3').text.strip() for i in data]
    locs = [' '.join(i.find('div', class_='offer-location').text.split()) for i in data]
    data_zip = zip(urls, titles, locs)

    data_dict = {}
    for i in data_zip:
        data_dict[meta['urls']['job']+i[0]] = {'Title':i[1], 'Location':i[2]}

    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    # get total number of jobs and pages to loop through and parse first page of results
    response = scrape_funcs.pull('get', url=meta['urls']['page'],
                                 headers=meta['requests']['headers'], params=meta['requests']['url'])

    bs_obj = BeautifulSoup(response.content, 'html.parser')

    num_jobs = int(bs_obj.find('span', class_='nb-total spanGreen').text)
    pagesize = len(bs_obj.find_all('h3', class_='title-4'))
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(bs_obj)

    # compile subsequent pages
    for i in range(2, pages+1):
        meta['requests']['url']['page'] = i
        response = scrape_funcs.pull('get', url=meta['urls']['page'],
                                     headers=meta['requests']['headers'], params=meta['requests']['url'])

        bs_obj = BeautifulSoup(response.content, 'html.parser')
        jobs_dict.update(jobs(bs_obj))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)