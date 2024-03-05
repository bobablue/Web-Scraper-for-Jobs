import os
import datetime
from bs4 import BeautifulSoup

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'chars':'+-',

        'requests':{'url':{'office_locations':'Asia+Pacific--Singapore', 'view_type':'list'}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(soup_obj):
    data = soup_obj.find_all('tr', class_='TableRow')
    data_dict = {}
    for i in data:
        job = i.find('a', class_='Link JobsListings__link')
        if job:
            data_dict[meta['urls']['job'] + job['href']] = {'Title':job.text,
                                                            'Job Function':i.find('li', class_='List__item ListItem JobsListings__departmentsListItem').text.strip(),
                                                            'Location':i.find('span', class_='JobsListings__locationDisplayName').text.strip()}
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], json_decode=True,
                                 params=scrape_funcs.encode(meta['requests']['url'], meta['chars']))

    bs_obj = BeautifulSoup(response['html'], 'html.parser')
    jobs_dict = jobs(bs_obj)
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)