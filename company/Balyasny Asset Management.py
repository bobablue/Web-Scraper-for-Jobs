import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),

        'requests':{'post':{'message':'{"actions":[{"descriptor":"aura://ApexActionController/ACTION$execute",\
                                        "params":{"classname":"BamJobRequisitionInfoDataService",\
                                                  "method":"searchJobRequisitions",\
                                                  "params":{"isVendorPortal":false,\
                                                            "site":"BAM Website",\
                                                            "locationFilters":["Singapore"]}}}]}',

                            'aura.context':'{"app":"siteforce:communityApp"}',
                            'aura.token':'null'}}}

#%% functions
#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    data_dict = {}
    for i in json_obj:

        url = f"{meta['urls']['job']}{i['Job_Req_Title_in_URL__c']}_{i['Requisition_Number__c']}"

        loc = i['Job_Requisitions_Locations__r']
        loc = sorted([' '.join(x['Location__r']['External_Name__c'].split()) for x in loc])
        loc = ' | '.join(loc)

        data_dict[url] = {'Title':i['Name'], 'Location':loc}

    return(data_dict)

#%%
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('post', url=meta['urls']['page'], data=meta['requests']['post'], json_decode=True)
    jobs_dict = jobs(response['actions'][0]['returnValue']['returnValue'])
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)