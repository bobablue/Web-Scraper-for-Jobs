import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'job_max':20, # 20 is hard limit

        'requests':{'post':{'limit':None, 'offset':0,
                            'appliedFacets':{'locations':['6ebadd30518d011ed3a5ed8337780000',
                                                          'b9d1c4463c030100fcbea274454b0000']}}}}

meta['requests']['post']['limit'] = meta['job_max']

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:

        # location missing in some posts
        try:
            loc = i['locationsText']
        except KeyError:
            loc = '' # json cannot store None/nan

        data_dict[meta['urls']['job']+i['externalPath']] = {'Title':i['title'], 'Location':loc}
        data_dict = scrape_funcs.clean_loc(data_dict)
    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('post', json_decode=True, url=meta['urls']['page'], json=meta['requests']['post'])

    num_jobs = response['total']
    pagesize = len(response['jobPostings'])
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(response['jobPostings']) # parse first page

    # compile subsequent pages
    for i in range(1,pages):
        meta['requests']['post']['offset'] = i * pagesize
        response = scrape_funcs.pull('post', json_decode=True, url=meta['urls']['page'], json=meta['requests']['post'])
        jobs_dict.update(jobs(response['jobPostings']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)