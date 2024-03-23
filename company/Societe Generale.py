import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'cookie':{'headers':{'X-Proxy-URL':'https://sso.sgmarkets.com/sgconnect/oauth2/access_token',
                                         'Authorization-API':''},

                              'data':{'grant_type':'client_credentials', 'scope':'api.corpsrc-00257.v1'}},

                    'headers':{'X-Proxy-URL':'https://api.socgen.com/business-support/it-for-it-support/cognitive-service-knowledge/api/v1/search-profile'},

                    'json':{'profile':'ces_profile_sgcareers',
                            'responseType':'SearchResult',
                            'query':{'skipCount':100,'skipFrom':0,
                                     'advanced':[{'type':'simple','name':'sourcestr6','op':'eq','value':'job'},
                                                 {'type':'multi','name':'sourcecsv1','op':'eq','values':['SGP']}]}}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        data_dict[i['resulturl']] = {'Title':i['title'],
                                     'Job Function':i['sourcestr10'],
                                     'Location':i['sourcecsv1']}
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    # get cookie and access token
    cookie = scrape_funcs.pull('post', url=meta['urls']['page'],
                               headers=meta['requests']['cookie']['headers'], data=meta['requests']['cookie']['data'])

    cookie = {**cookie.json(), **cookie.cookies.get_dict()}

    # update headers with cookie token
    headers = meta['requests']['headers'] | {'Authorization-API':f"{cookie['token_type']} {cookie['access_token']}"}

    # get all jobs
    response = scrape_funcs.pull('post', url=meta['urls']['page'], headers=headers, json=meta['requests']['json']).json()

    # if num_jobs>default in skipCount, update json_data and call again with updated number
    num_jobs = response['TotalCount']
    if num_jobs>meta['requests']['json']['query']['skipCount']:
        meta['requests']['json']['query']['skipCount'] = num_jobs
        response = scrape_funcs.pull('post', url=meta['urls']['page'], headers=headers, json=meta['requests']['json']).json()

    jobs_dict = jobs(response['Result']['Docs'])
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)