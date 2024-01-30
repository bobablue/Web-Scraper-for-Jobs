import os
import datetime
import re

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'cookie':{'partnerid':'25008', 'siteid':'5012', 'PageType':'searchResults'},

                    'headers':{},

                    'post':{'PartnerId':'25008', 'SiteId':'5012', 'Location':'Singapore',
                            'pageNumber':1, 'KeywordCustomSolrFields':'FORMTEXT21,Department,JobTitle',
                            'LocationCustomSolrFields':'FORMTEXT23'},

                    'extract':{'department':'Department', 'jobtitle':'Title',
                               'formtext23':'Location', 'formtext21':'Team'}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_dict):
    data_dict = {json_dict['Link']:{}}

    # every key in extract
    for qn in json_dict['Questions']:
        if qn['QuestionName'] in meta['requests']['extract']:
            data_dict[json_dict['Link']].update({meta['requests']['extract'][qn['QuestionName']]:scrape_funcs.decode(qn['Value'].strip())})

    # combine department and team into 'job function', then remove former 2 keys
    data_dict[json_dict['Link']]['Job Function'] = data_dict[json_dict['Link']]['Department'] + '|' + data_dict[json_dict['Link']]['Team']
    for i in ['Department','Team']:
        data_dict[json_dict['Link']].pop(i, None)

    return(data_dict)

#%%
@scrape_funcs.track_status(__file__)
def get_jobs():
    # get RFT token and cookie to generate headers
    response = scrape_funcs.pull('post', url=meta['urls']['cookie'], params=meta['requests']['cookie'])

    meta['requests']['headers'] = {'RFT':re.compile(r'RequestVerificationToken" type="hidden" value="(.*)"').findall(response.text)[0],
                                   'Cookie':'; '.join(f'{k}={v}' for k,v in response.cookies.get_dict().items())}

    # get total number of jobs and pages to loop through and parse first page of results
    response = scrape_funcs.pull('post', json_decode=True, url=meta['urls']['page_1'],
                                 headers=meta['requests']['headers'], data=meta['requests']['post'])

    num_jobs = response['JobsCount']
    pagesize = len(response['Jobs']['Job'])
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = {}
    for i in response['Jobs']['Job']:
        jobs_dict.update(jobs(i))

    # compile jobs from all pages after first, into main dict (update post_data to include page number)
    for pg in range(2, pages+1):
        meta['requests']['post']['pageNumber'] = pg
        response = scrape_funcs.pull('post', json_decode=True, url=meta['urls']['page_n'],
                                     headers=meta['requests']['headers'], data=meta['requests']['post'])

        for i in response['Jobs']['Job']:
            jobs_dict.update(jobs(i))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)