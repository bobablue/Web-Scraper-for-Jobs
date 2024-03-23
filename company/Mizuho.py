import os
import datetime
import re

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'cookie':{'partnerid':'26255', 'siteid':'5812'},

                    'post':{'PartnerId':'26255', 'SiteId':'5812', 'pageNumber':1,
                            'KeywordCustomSolrFields':'JobTitle,FORMTEXT1,'},

                    'extract':{'jobtitle':'Title', 'formtext1':'Job Function'},

                    # assume this id maps to singapore
                    'location':{'1033':'Singapore'}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:
        data_dict[i['Link']] = {'Location':meta['requests']['location'][i['localeId']]}

        # every key in extract
        for qn in i['Questions']:
            if qn['QuestionName'] in meta['requests']['extract']:
                data_dict[i['Link']].update({meta['requests']['extract'][qn['QuestionName']]:scrape_funcs.decode(qn['Value'].strip())})

    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    # get RFT token and cookie to generate headers
    response = scrape_funcs.pull('post', url=meta['urls']['cookie'], params=meta['requests']['cookie'])

    meta['requests']['headers'] = {'RFT':re.compile(r'RequestVerificationToken" type="hidden" value="(.*)"').findall(response.text)[0],
                                   'Cookie':'; '.join(f'{k}={v}' for k,v in response.cookies.get_dict().items())}

    response = scrape_funcs.pull('post', json_decode=True, url=meta['urls']['page_1'],
                                 headers=meta['requests']['headers'], data=meta['requests']['post'])

    num_jobs = response['JobsCount']
    pagesize = len(response['Jobs']['Job'])
    pages = num_jobs//pagesize + (num_jobs % pagesize>0)

    jobs_dict = jobs(response['Jobs']['Job']) # parse first page

    # compile subsequent pages
    for i in range(2,pages+1):
        meta['requests']['post']['pageNumber'] = i
        response = scrape_funcs.pull('post', json_decode=True, url=meta['urls']['page_n'],
                                     headers=meta['requests']['headers'], data=meta['requests']['post'])

        jobs_dict.update(jobs(response['Jobs']['Job']))

    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)