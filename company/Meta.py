import os
import datetime
import re

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'headers':{'X-FB-LSD':None},

                    'post':{'lsd':None,
                            'variables':'{"search_input":{"offices":["Singapore"],"page":1,"results_per_page":null}}',
                            'doc_id':'9114524511922157'}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        data_dict[meta['urls']['job'] + i['id']] = {'Title':i['title'].strip(),
                                                    'Job Function':' | '.join(i['sub_teams']),
                                                    'Location':' | '.join(i['locations'])}
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    # get tokens
    response = scrape_funcs.pull('get', url=meta['urls']['cookie'])

    token = response.text
    token = re.search(r'\["LSD",\[\],{"token":"(.+)"},323]', token).group(1)

    # update parameters with token
    meta['requests']['headers']['X-FB-LSD'] = token
    meta['requests']['post']['lsd'] = token

    response = scrape_funcs.pull('post', url=meta['urls']['page'], headers=meta['requests']['headers'],
                                 data=meta['requests']['post'], json_decode=True)

    jobs_dict = jobs(response['data']['job_search'])
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)