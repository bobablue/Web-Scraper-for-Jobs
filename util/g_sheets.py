import gspread
from google.oauth2.service_account import Credentials

#%% static data and variables for google sheets API
account = {'scope':['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive']}

#%%
def auth(path_to_key):
    account['credentials'] = Credentials.from_service_account_file(path_to_key, scopes=account['scope'])
    account['auth'] = gspread.authorize(account['credentials'])

#%%
def update(df, g_sheet_key, sheet_name):
    data = {}

    data['wb'] = account['auth'].open_by_key(g_sheet_key)

    data['dataframe'] = df.reset_index(names=['Index'])
    data['dataframe']['Index'] = data['dataframe']['Index'] + 1
    data['dataframe'] = data['dataframe'].fillna('') # json format should not have nans

    if 'Date Scraped' in list(data['dataframe']):
        data['dataframe']['Date Scraped'] = data['dataframe']['Date Scraped'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # https://docs.gspread.org/en/latest/api/models/worksheet.html#gspread.worksheet.Worksheet.update
    # clear entire worksheet and resize it according to the shape of the dataframe, then paste new data
    data[sheet_name] = data['wb'].worksheet(sheet_name)
    data[sheet_name].clear()
    data[sheet_name].resize(rows=len(data['dataframe']), cols=len(list(data['dataframe'])))
    data[sheet_name].update(range_name='',
                            values=[data['dataframe'].columns.values.tolist()] + data['dataframe'].values.tolist())

    # reset the filters, as new rows would not be in the filter data range
    reset_filter = [{'setBasicFilter':{'filter':{'range':{'sheetId':data[sheet_name].id,
                                                          'startColumnIndex':0,
                                                          'endColumnIndex':len(list(data['dataframe']))}}}}]

    data['wb'].batch_update({'requests':reset_filter})