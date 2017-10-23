from aiohttp import web
import aiohttp
import asyncio
import requests
import json

from file_currency_symbols import currency_symbols

# global variable to store currency codes
currency_codes = []
def get_currency_codes():
    """r.

    Keyword arguments:
    real -- the real part (default 0.0)
    imag -- the imaginary part (default 0.0)
    """
    payload = {'format': 'json'}
    req = requests.get('https://finance.yahoo.com/webservice/v1/symbols/allcurrencies/quote', \
        params=payload)

    req = req.json()

    global currency_codes
    for elem in req['list']['resources']:
        currency_codes.append(elem['resource']['fields']['symbol'])


async def get_ex_rate(session, cur_from, cur_to):
    """Get exchange rate between two currencies

    Keyword arguments:
    session -- aiohttp.ClientSession() instance
    cur_from -- input currency
    cur_to -- output currency
    """ 
    payload = {'s': cur_from+cur_to+'=X', 'e': '.csv', 'f': 'nl1'}
    url = 'https://finance.yahoo.com/d/quotes.csv'

    async with session.get(url, params=payload, timeout=5) as response:
        return await response.text()


async def get_all_ex_rates(session, cur_from):
    """Get all exchange rates for base currency

    Keyword arguments:
    session -- aiohttp.ClientSession() instance
    cur_from -- base currency
    """ 
    global currency_codes
    cur_query = [cur_from + cur for cur in currency_codes if cur != cur_from + '=X']
    cur_query = ','.join(cur_query)
    
    payload = {'s': cur_query, 'e': '.csv', 'f': 'nl1'}
    url = 'https://finance.yahoo.com/d/quotes.csv'

    async with session.get(url, params=payload, timeout=5) as response:
        return await response.text()


def convert(data, amount):
    """Convert money and construct dictionary

    Keyword arguments:
    data -- exchange rates data
    amount -- amount of money to convert
    """ 
    dic = {"input": {"amount": float(amount), "currency": ""},
                "output": {}}

    lst = data.strip().split('\n')
    dic['input']['currency'] = lst[0][1:4]
    for elem in lst:
        row = elem.split(',')
        try:
            dic['output'][row[0][5:8]] = float(row[1]) * amount
        except ValueError:
            continue

    return dic


async def handle(request):
    """Handler for get request

    Keyword arguments:
    request -- get request
    """ 
    amount = request.query['amount']
    try:
        amount = float(amount)
    except ValueError as e:
        return aiohttp.web.HTTPBadRequest(reason=str(e))

    if amount < 0:
        return aiohttp.web.HTTPBadRequest(reason='ValueError: Negative amount.')
    
    _from = request.query['input_currency']
    if _from+'=X' not in currency_codes and _from not in currency_symbols:
        return aiohttp.web.HTTPBadRequest(reason='Invalid input currency code or symbol.')
    
    if _from in currency_symbols:
        _from = currency_symbols[_from]

    to = ''
    if 'output_currency' in request.query:
        to = request.query['output_currency']
        if to+'=X' not in currency_codes and to not in currency_symbols:
            return aiohttp.web.HTTPBadRequest(reason='Invalid output currency code or symbol.')

    if to in currency_symbols:
        to = currency_symbols[to]

    # since exchange rates are constantly changing let's not use redis, 
    # but pull new data for every request
    async with aiohttp.ClientSession() as session:
        data = {}
        if to != '':
            ex_rates = await get_ex_rate(session, _from, to)
            data = convert(ex_rates, amount)
        else:
            ex_rates = await get_all_ex_rates(session, _from)
            data = convert(ex_rates, amount)

        return web.json_response(data)


get_currency_codes()
app = aiohttp.web.Application()
app.router.add_get('/currency_converter', handle)
web.run_app(app, host='127.0.0.1', port=8080)