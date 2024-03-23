import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
# PositionLocation.Country 71:'United Kingdom', 189:'Singapore'
# PositionLocation.City 1628:'Frankfurt am Main', 1698:'Frankfurt'
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'locations':{'PositionLocation.Country':[189]},

        'requests':{'json':{'SearchParameters':{'CountItem':100,
                                                'MatchedObjectDescriptor':['PositionID','PositionTitle','OrganizationName']},
                            'SearchCriteria':None}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    key = 'MatchedObjectDescriptor'
    data = [i[key] for i in json_obj['SearchResult']['SearchResultItems'] if key in i]
    data_dict = {}
    for d in data:
        data_dict[meta['urls']['job'] + d['PositionID']] = {'Title':scrape_funcs.decode(d['PositionTitle']),
                                                            'Location':d['OrganizationName']}
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    jobs_dict = {}
    for i,j in meta['locations'].items():
        meta['requests']['json']['SearchCriteria'] = [{'CriterionName':i, 'CriterionValue':j}]
        response = scrape_funcs.pull('get', json_decode=True, url=meta['urls']['page'], json=meta['requests']['json'])

        # if num_jobs>default in CountItem, update json_data and call again with updated number
        if response['SearchResult']['SearchResultCountAll']>meta['requests']['json']['SearchParameters']['CountItem']:
            meta['requests']['json']['SearchParameters']['CountItem'] = response['SearchResult']['SearchResultCountAll']
            response = scrape_funcs.pull('get', json_decode=True, url=meta['urls']['page'], json=meta['requests']['json'])

        jobs_dict.update(jobs(response))
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)