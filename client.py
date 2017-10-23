import asyncio
import click
import aiohttp
from aiohttp import web
import json
import sys

async def fetch(session, amount, _from, to):
  """GET request

  Keyword arguments:
  session -- aiohttp.ClientSession() instance
  amount -- amount of money to convert
  _from -- input currency
  to -- output currency
  """ 
  payload = {'amount': amount, 'input_currency': _from}
  if to is not None:
    payload['output_currency'] = to

  try:
    async with session.get('http://127.0.0.1:8080/currency_converter', \
      params=payload, timeout=10) as response:

      # raise exception for all http error status codes
      response.raise_for_status()
      return await response.text()
  except aiohttp.client_exceptions.ClientConnectorError as e:
    raise e


async def main(amount, _from, to):
    """Create a aiohttp session and fetch data

    Keyword arguments:
    amount -- amount of money to convert
    _from -- input currency
    to -- output currency
    """ 
    async with aiohttp.ClientSession() as session:
      try:
        response = await fetch(session, amount, _from, to)
        print(json.dumps(json.loads(response), sort_keys=True, indent=4))
      except aiohttp.web.HTTPError as e:
        print(e, file=sys.stderr)
      except aiohttp.client_exceptions.ClientConnectorError as e:
        print(e, file=sys.stderr)


@click.command(options_metavar='<options>')
@click.option('--amount', required=True, type=float, help='An amount of money to convert.')
@click.option('--input_currency', required=True, help='3 letters code or symbol of currency.')
@click.option('--output_currency', required=False, help='3 letters code or symbol of currency.')
def arg_parse(amount, input_currency, output_currency):
  """Parse cmd arguments and run asyncio loop"""
  loop = asyncio.get_event_loop()
  loop.run_until_complete(main(str(amount), str(input_currency), output_currency))
  loop.close()

if __name__ == '__main__':
  arg_parse()