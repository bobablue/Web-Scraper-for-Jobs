import gspread
from google.oauth2.service_account import Credentials

#%% static data and variables for google sheets API
account = {'scope':['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive']}

#%%
def auth(path_to_key):
    account['credentials'] = Credentials.from_service_account_file(path_to_key, scopes=account['scope'])
    account['auth'] = gspread.authorize(account['credentials'])

#%%
def update(df, g_sheet_key):
    data = {}

    data['wb'] = account['auth'].open_by_key(g_sheet_key)

    data['dataframe'] = df.copy()
    data['dataframe'] = data['dataframe'].fillna('')
    data['dataframe']['Date Scraped'] = data['dataframe']['Date Scraped'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # https://docs.gspread.org/en/latest/api/models/worksheet.html#gspread.worksheet.Worksheet.update
    data['All'] = data['wb'].worksheet('All')
    data['All'].clear()
    data['All'].resize(rows=len(df))
    data['All'].update(range_name='', values=[data['dataframe'].columns.values.tolist()] + data['dataframe'].values.tolist())