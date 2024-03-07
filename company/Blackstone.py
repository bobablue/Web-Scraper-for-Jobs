import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':20, # 20 default and cannot be increased

        'requests':{'headers':{'Content-Type':'application/json'},

                    'post':{'limit':None,'offset':0,
                            'appliedFacets':{'locations':['ef375a2335bb011b9951cf065e1fa62b']}}}}

meta['requests']['post']['limit'] = meta['job_max']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        data_dict[meta['urls']['job'] + i['externalPath']] = {'Title':i['title'],
                                                              'Job Function':i['bulletFields'][-1],
                                                              'Location':i['locationsText']}
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('post', url=meta['urls']['page'], json_decode=True,
                                 headers=meta['requests']['headers'], json=meta['requests']['post'])

    num_jobs = response['total']
    pagesize = meta['job_max']
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(response['jobPostings']) # parse first page

    # compile subsequent pages
    for i in range(1,pages):
        meta['requests']['post']['offset'] = i * pagesize
        response = scrape_funcs.pull('post', url=meta['urls']['page'], json_decode=True,
                                     headers=meta['requests']['headers'], json=meta['requests']['post'])

        jobs_dict.update(jobs(response['jobPostings']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)