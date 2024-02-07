import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'country':['SG']}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(data):
    data_dict = [i for i in data if any(i['title'].startswith(x) for x in meta['country'])]
    data_dict = {i['title'].split(' - ')[-1]:i['postings'] for i in data_dict}

    jobs_dict = {}
    for cty,job_list in data_dict.items():
        for job in job_list:

            if 'department' in job['categories'].keys():
                job_func = f"{job['categories']['department']}: {job['categories']['team']}"
            else:
                job_func = ''

            jobs_dict[job['hostedUrl']] = {'Title':job['text'], 'Job Function':job_func, 'Location':cty}

    return(jobs_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], json_decode=True)
    jobs_dict = jobs(response)
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)