import aiohttp
import asyncio
import platform
import argparse
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('errors.log'), logging.StreamHandler()])

class HttpError(Exception):
    pass

async def request(url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientError as err:
            raise HttpError(f'HTTP error occurred: {url}', str(err))

async def main(num_days):
    results = []

    for i in range(num_days - 1, -1, -1):
        day = datetime.now() - timedelta(days=i)
        shift = day.strftime("%d.%m.%Y")
        try:
            response = await request(f'https://api.privatbank.ua/p24api/exchange_rates?date={shift}')
            if 'exchangeRate' in response:
                euro = next((rate for rate in response['exchangeRate'] if rate['currency'] == 'EUR'), None)
                usd = next((rate for rate in response['exchangeRate'] if rate['currency'] == 'USD'), None)
                result = {
                    shift: {
                        'EUR': {
                            'sale': euro['saleRate'],
                            'purchase': euro['purchaseRate']
                        },
                        'USD': {
                            'sale': usd['saleRate'],
                            'purchase': usd['purchaseRate']
                        }
                    }
                }
                results.append(result)
            else:
                logging.error(f'Exchange rates not found in API response for {shift}')
        except HttpError as err:
            logging.error(err)

    return results

async def save_to_file(results):
    with open('exchange_rates.txt', 'w') as file:
        for item in results:
            file.write(str(item) + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('num_days', type=int, help='Number of days to fetch exchange rates including today')

    args = parser.parse_args()

    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    result = asyncio.run(main(args.num_days))
    if result:
        for item in result:
            print(item)
        asyncio.run(save_to_file(result))
