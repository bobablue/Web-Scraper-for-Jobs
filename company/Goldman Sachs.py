import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':250, # 250 is hard limit

        'requests':{'post':{'operationName':'GetRoles',

                            'variables':{'searchQueryInput':{'page':{'pageSize':None,'pageNumber':0},

                                                             'filters':[{'filterCategoryType':'LOCATION',
                                                                         'filters':[{'filter':'Singapore'}]}],

                                                             'experiences':['PROFESSIONAL','EARLY_CAREER']}},

                            'query':'query GetRoles($searchQueryInput: RoleSearchQueryInput!) {roleSearch(searchQueryInput: $searchQueryInput) {totalCount items {roleId jobTitle jobFunction locations {country} externalSource {sourceId}}}}'}}}

meta['requests']['post']['variables']['searchQueryInput']['page']['pageSize'] = meta['job_max']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        data_dict[meta['urls']['job'] + i['externalSource']['sourceId']] = {'Title':i['jobTitle'],
                                                                            'Job Function':i['jobFunction'],
                                                                            'Location':' | '.join([j['country'] for j in i['locations']])}
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('post', url=meta['urls']['page'], json=meta['requests']['post'], json_decode=True)
    response = response['data']['roleSearch']

    num_jobs = response['totalCount']
    pagesize = meta['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(response['items']) # parse first page

    # compile subsequent pages
    for i in range(1,pages):
        meta['requests']['post']['variables']['searchQueryInput']['page']['pageNumber'] = i
        response = scrape_funcs.pull('post', url=meta['urls']['page'], json=meta['requests']['post'], json_decode=True)
        response = response['data']['roleSearch']
        jobs_dict.update(jobs(response['items']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)