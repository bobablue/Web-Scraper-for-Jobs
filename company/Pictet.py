import os
import datetime
import re

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'locations':['singapore'],

        'requests':{'headers':{'viewid':'/ui/rcmcareer/pages/careersite/career.jsp.xhtml'},

                    'data':{'callCount':1,
                            'c0-scriptName':'careerJobSearchControllerProxy',
                            'c0-methodName':'search',
                            'c0-id':0,
                            'c0-e5':'string:100',
                            'c0-e1':'Object_Object:{pageSize:reference:c0-e5}',
                            'c0-param0':'Object_Object:{pagination:reference:c0-e1}',
                            'batchId':1}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(response_obj):

    # regex patterns to extract job data
    patterns = {'url':re.compile(r'\.id=(\d*);'),
                'title':re.compile(r'title="(.*)"'),
                'descriptors':re.compile(r'shortVal="(.*)"')}

    # extract data fields in list type from response object
    urls = [meta['urls']['job'] + url for url in patterns['url'].findall(response_obj)]
    titles = patterns['title'].findall(response_obj)
    location = patterns['descriptors'].findall(response_obj)[0::4]
    jobfunc = patterns['descriptors'].findall(response_obj)[1::4]

    # string cleanup
    titles = [i.replace('\\','') for i in titles]
    jobfunc = [scrape_funcs.decode(i) for i in jobfunc]

    # combine all lists of data fields into dictionary
    data = zip(urls, titles, location, jobfunc)
    data_dict = {}
    for d in data:
        data_dict[d[0]] = {'Title':d[1], 'Location':d[2], 'Job Function':d[3]}

    data_dict = scrape_funcs.restrict_loc(data_dict, meta['locations'])
    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    # get cookie, ajax token, and sessionid
    cookie = scrape_funcs.pull('post', url=meta['urls']['cookie'])

    meta['requests']['headers'].update({'cookie':'; '.join(f'{k}={v}' for k,v in cookie.cookies.get_dict().items()),
                                        'x-ajax-token':re.compile(r'ajaxSecKey="(.*)";var').findall(cookie.text)[0]})

    meta['requests']['data'].update({'scriptSessionId':re.compile(r'jsessionid=(.+)\?').findall(cookie.text)})

    # get all jobs
    response = scrape_funcs.pull('post', url=meta['urls']['page'],
                                 headers=meta['requests']['headers'], data=meta['requests']['data'])

    # if default in c0-e5<num_jobs, update params and call again with updated c0-e5
    num_jobs = int(re.compile(r's0.postingCount="(\d+)"').findall(response.text)[0])
    if num_jobs>int(re.compile(r'(\d+)').findall(meta['requests']['data']['c0-e5'])[0]):
        meta['requests']['data']['c0-e5'] = re.sub(r'(\d+)', f'{num_jobs}', meta['requests']['data']['c0-e5'])
        response = scrape_funcs.pull('post', url=meta['urls']['page'],
                                     headers=meta['requests']['headers'], data=meta['requests']['data'])

    jobs_dict = jobs(response.text)
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)