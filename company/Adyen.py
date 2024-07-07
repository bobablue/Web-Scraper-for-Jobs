"""is there a better way to get the data? convoluted way currently gets all URLs then loads each URL to extract info."""
import os
import datetime
from bs4 import BeautifulSoup
import re
from concurrent.futures import ThreadPoolExecutor

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'locations':['singapore']}

#%% functions
#%%
def get_info(job_url):
    response = scrape_funcs.pull('get', url=job_url)
    bs_obj = BeautifulSoup(response.content, 'html.parser')

    title = bs_obj.find('h1', {'class':'ds-heading-medium ds-md-heading-large'}).text.strip()

    loc_job_func = bs_obj.find('div', {'class':'ds-font-weight-bold ds-margin-y-24 ds-display-flex ds-align-items-center'})
    loc_job_func = loc_job_func.text.strip().split('\n')
    loc_job_func = [i.strip() for i in loc_job_func if i.strip()!='']

    info = {'Title':title, 'Job Function':loc_job_func[0], 'Location':loc_job_func[1]}
    return(info)

#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(js_obj):
    urls = js_obj.text.encode().decode('unicode-escape')
    urls = re.findall(r'"/careers(/vacancies/[^"]*)"', urls)
    jobs_all = {meta['urls']['job']+url:{} for url in urls}

    # get each url's info: title, job function, location
    with ThreadPoolExecutor(max_workers=min(os.cpu_count()*5, len(jobs_all))) as executor:
        for i in list(jobs_all):
            jobs_all[i] = executor.submit(get_info, i)

    jobs_all = {k:v.result() for k,v in jobs_all.items()}

    jobs_filtered = scrape_funcs.restrict_loc(jobs_all, meta['locations'])
    return(jobs_filtered)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    # get js payload link
    response = scrape_funcs.pull('get', url=meta['urls']['cookie'])
    payload = re.search(r'/_nuxt/static/\d+/manifest\.js', response.text).group(0)

    # pull full list of jobs, which are then filtered to selected locations
    response = scrape_funcs.pull('get', url=meta['urls']['page']+payload)
    jobs_dict = jobs(response)
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)