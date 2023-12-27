import common.scrapefuncs as sf
import common.errorhandling as errorhandling
import os
import datetime

#%% static data
# 71:'United Kingdom', 189:'Singapore', 1628:'Frankfurt am Main', 1698:'Frankfurt'
meta = {'urls':sf.get_urls('urls.csv', os.path.splitext(os.path.basename(__file__))[0]),
        'locations':{'PositionLocation.Country':[71, 189], 'PositionLocation.City':[1628, 1698]}}

# requests parameters
json_data = {'SearchParameters':{'CountItem':100,
             'MatchedObjectDescriptor':['PositionID','PositionTitle','OrganizationName']},
             'SearchCriteria':None}

#%% functions
#%%
@errorhandling.data_error
@sf.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def extract_data(json_obj):
    key = 'MatchedObjectDescriptor'
    data = [i[key] for i in json_obj['SearchResult']['SearchResultItems'] if key in i]
    data_dict = {}

    for d in data:
        data_dict[meta['urls']['job'] + d['PositionID']] = {'Title':sf.decode(d['PositionTitle']),
                                                            'Location':d['OrganizationName']}

    return(data_dict)

#%%
def get_jobs():
    jobs_dict = {}
    for i,j in meta['locations'].items():
        json_data['SearchCriteria'] = [{'CriterionName':i, 'CriterionValue':j}]
        response = sf.pull('get', json_decode=True, url=meta['urls']['page'], json=json_data)

        # if no_jobs>default in CountItem, update json_data and call again with updated number
        if response['SearchResult']['SearchResultCountAll']>json_data['SearchParameters']['CountItem']:
            json_data['SearchParameters']['CountItem'] = response['SearchResult']['SearchResultCountAll']
            response = sf.pull('get', json_decode=True, url=meta['urls']['page'], json=json_data)

        jobs_dict.update(extract_data(response))
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    sf.to_json(meta['urls']['company'], jobs_dict)