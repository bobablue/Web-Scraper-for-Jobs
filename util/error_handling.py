import requests

#%% requests non-response or timeout
def requests_error(func):
    def wrapper(*args, **kwargs):
        try:
            output = func(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            return(e)
        return(output)
    return(wrapper)

#%% empty json entries from requests response
def data_error(func):
    def wrapper(*args, **kwargs):
        try:
            output = func(*args, **kwargs)
        except KeyError as e:
            return(e)
        return(output)
    return(wrapper)