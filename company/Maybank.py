import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'headers':{},
                    'json': {'searchKeywords':{'jobCountry':'Singapore'}}}}

meta['requests']['headers']['Portal-Id'] = scrape_funcs.pull('get', json_decode=True, url=meta['urls']['cookie'])['payload'][0]['portalId']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_list):
    data_dict = {}
    for data in json_list:
        data_dict[meta['urls']['job']+str(data['id'])] = {'Title':data['title'],
                                                          'Location':data['country'],
                                                          'Job Function':data['specialization']}
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('post', json_decode=True, url=meta['urls']['page'],
                                 headers=meta['requests']['headers'], json=meta['requests']['json'])['payload']

    jobs_dict = jobs(response)
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)