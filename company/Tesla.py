import os
import datetime

# import custom scripts (https://stackoverflow.com/a/38455936)
if __name__=='__main__' and __package__ is None:
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import scrape_funcs, error_handling

#%% static data
meta = {'urls':scrape_funcs.get_urls(os.path.join(os.path.dirname(__file__), 'urls.csv'), os.path.splitext(os.path.basename(__file__))[0]),
        'locations':['singapore'],

        'requests':{'headers':{'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:127.0) Gecko/20100101 Firefox/127.0'}}}

#%% functions
#%% https://stackoverflow.com/a/19871956
def find_key(node, key):
    if isinstance(node, list):
        for i in node:
            for x in find_key(i, key):
                yield x
    elif isinstance(node, dict):

        if 'name' in node:
            # typically country, city. but US is country, state, city, with a 'name' key in city.
            node['id'] = 'US'

            # add state name to city name in case city name duplicates (13 Wilmington cities in US)
            node['cities'] = {f"{k}, {node['name']}":v for k,v in node['cities'].items()}

        if key in node:
            yield {node['id']: node[key]}
        for j in node.values():
            for x in find_key(j, key):
                yield x

#%% '32046' is unmapped
def country_map(json_obj):
    iso2 = json_obj['lookup']['sites']

    countries = json_obj['geo']
    countries = find_key(countries, 'cities')
    countries = [i for i in countries]

    # dict of {country:{city_name:[loc_ids]}}
    countries_flat = {}
    for i in countries:
        for country_name, cities in i.items():
            country_name = iso2[country_name] # change from country 2-letter code to full name
            if country_name not in countries_flat:
                countries_flat[country_name] = cities
            else:
                countries_flat[country_name].update(cities)

    # flatten to {loc_id:country}
    id_country = {}
    for country_name, cities in countries_flat.items():
        for city, locs in cities.items():
            id_country.update({loc_id:f"{country_name} | {city}" for loc_id in locs})
    return(id_country)

#%%
@error_handling.data_error
@scrape_funcs.metadata(meta['urls']['company'], datetime.datetime.today().replace(microsecond=0))
def jobs(json_obj):
    lookup = json_obj['lookup']
    locs = country_map(json_obj)
    data_dict = {}
    for i in json_obj['listings']:
        data_dict[meta['urls']['job']+i['id']] = {'Title':i['t'],
                                                  'Location':locs[i['l']] if i['l'] in locs else i['l'],
                                                  'Job Function':lookup['departments'][i['dp']]}

    data_dict = scrape_funcs.restrict_loc(data_dict, meta['locations'])
    return(data_dict)

#%% get all jobs
@scrape_funcs.num_jobs(__file__)
def get_jobs():
    response = scrape_funcs.pull('get', url=meta['urls']['page'], headers=meta['requests']['headers'], json_decode=True)
    jobs_dict = jobs(response)
    return(jobs_dict)

#%%
if __name__=='__main__':
    jobs_dict = get_jobs()
    scrape_funcs.to_json(meta['urls']['company'], jobs_dict)