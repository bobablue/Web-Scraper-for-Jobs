import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'url':{'country':{'flags':16, 'search_channel':2},
                           'dept':{'search_channel':2},
                           'jobs':{'post_type':4, 'limit':100, 'region_ids':24}}}}

meta['urls'].update({'country':'https://ats.workatsea.com/ats/api/v1/user/meta/slice/?',
                     'dept':'https://ats.workatsea.com/ats/api/v1/user/dept/job_count/?'})

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(jobs_obj, countries_obj, depts_obj):
    data_dict = {}
    data_dict[meta['urls']['job'].replace('job_id', jobs_obj['job_id'])] = {'Title':jobs_obj['job_name'],
                                                                            'Location':countries_obj[jobs_obj['region_id']],
                                                                            'Job Function':depts_obj[jobs_obj['department_id']]}
    return(data_dict)

#%% mapping of id to countries
def get_countries():
    response = scrape_funcs.pull('get', json_decode=True,
                                 url=meta['urls']['country'], params=meta['requests']['url']['country'])

    countries = {}
    for i in response['data']['flat_locations']:
        countries[i['region_id']] = i['region_name']

    return(countries)

#%% mapping of id to departments
def get_depts():
    response = scrape_funcs.pull('get', json_decode=True,
                                 url=meta['urls']['dept'], params=meta['requests']['url']['dept'])

    depts = {}
    for i in response['data']:
        depts[i['dept_id']] = i['dept_name']

    return(depts)

#%% get all jobs
@scrape_funcs.track_status(__file__)
def get_jobs():
    countries = get_countries()
    depts = get_depts()

    response = scrape_funcs.pull('get', json_decode=True,
                                 url=meta['urls']['page'], params=meta['requests']['url']['jobs'])

    # if num_jobs>default in limit, update and call again with updated limit
    num_jobs = response['data']['total_count']
    if num_jobs>meta['requests']['url']['jobs']['limit']:
        meta['requests']['url']['jobs']['limit'] = num_jobs
        response = scrape_funcs.pull('get', json_decode=True,
                                     url=meta['urls']['page'], params=meta['requests']['url']['jobs'])

    jobs_dict = {}
    for i in response['data']['job_list']:
        jobs_dict.update(jobs(i, countries, depts))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)