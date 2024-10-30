from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout
)
from colorama import *
from datetime import datetime, timedelta
from fake_useragent import FakeUserAgent
from random import randint
import asyncio, json, os, sys

class MoonRabbits:
    def __init__(self) -> None:
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Host': 'moonrabbits-api.backersby.com',
            'Origin': 'https://moonrabbits.backersby.com',
            'Pragma': 'no-cache',
            'Referer': 'https://moonrabbits.backersby.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': FakeUserAgent().random
        }

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_timestamp(self, message):
        print(
            f"{Fore.BLUE + Style.BRIGHT}[ {datetime.now().astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{message}",
            flush=True
        )

    async def generate_token(self, query: str):
        url = 'https://moonrabbits-api.backersby.com/v1/accounts/sync'
        data = json.dumps({'telegram_data':query,'invited_by':'6094625904'})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    response.raise_for_status()
                    generate_token = await response.json()
                    return {'cookie': response.headers['Set-Cookie'].split(';')[0], 'username': generate_token['username']}
        except (Exception, ClientResponseError) as error:
            self.print_timestamp(
                f"{Fore.YELLOW + Style.BRIGHT}[ Failed To Process {query} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.RED + Style.BRIGHT}[ {str(error)} ]{Style.RESET_ALL}"
            )
            return None

    async def generate_tokens(self, queries):
        tasks = [self.generate_token(query) for query in queries]
        results = await asyncio.gather(*tasks)
        results = [result for result in results if result is not None]

        existing_accounts = {}
        if os.path.exists('accounts.json'):
            existing_accounts = {account['username']: account['cookie'] for account in json.load(open('accounts.json', 'r'))}

        for result in results:
            username = result['username']
            cookie = result['cookie']
            existing_accounts[username] = cookie

        json.dump([{'username': k, 'cookie': v} for k, v in existing_accounts.items()], open('accounts.json', 'w'), indent=4)

    async def load_from_json(self):
        try:
            return [(account['cookie'], account['username']) for account in json.load(open('accounts.json', 'r'))]
        except Exception as error:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Error Occurred While Loading JSON: {str(error)} ]{Style.RESET_ALL}")
            return []

    async def my_mrb(self, cookie: str):
        url = 'https://moonrabbits-api.backersby.com/v1/my-mrb'
        headers = {
            **self.headers,
            'Cookie': cookie
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers, ssl=False) as response:
                    response.raise_for_status()
                    return await response.json()
        except ClientResponseError as error:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching My MRB: {str(error)} ]{Style.RESET_ALL}")
            return None
        except Exception as error:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching My MRB: {str(error)} ]{Style.RESET_ALL}")
            return None

    async def my_tasks(self, cookie: str):
        url = 'https://moonrabbits-api.backersby.com/v1/my-tasks'
        headers = {
            **self.headers,
            'Cookie': cookie
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers, ssl=False) as response:
                    await asyncio.sleep(randint(3, 5))
                    response.raise_for_status()
                    my_tasks = await response.json()
                    for category, tasks in my_tasks.items():
                        for task in tasks:
                            await self.my_tasks_complete(cookie=cookie, task_id=task['id'], task_name=task['name'])
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching My Tasks: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching My Tasks: {str(error)} ]{Style.RESET_ALL}")

    async def my_tasks_complete(self, cookie: str, task_id: str, task_name: str):
        url = 'https://moonrabbits-api.backersby.com/v1/my-tasks/complete'
        data = json.dumps({'task_id':task_id})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'Cookie': cookie
        }
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    if response.status == 400:
                        error_my_tasks_complete = await response.json()
                        for count in ['5', '10', '30', '50', '100']:
                            if error_my_tasks_complete['message'] == f'Not enough friends. Invite at least {count} friends to claim the reward.':
                                return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Not Enough Friends. Invite At Least {count} Friends To Claim The Reward. ]{Style.RESET_ALL}")
                        if error_my_tasks_complete['message'] == 'Already completed task':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Already Completed {task_name} ]{Style.RESET_ALL}")
                        elif error_my_tasks_complete['message'] == 'Already completed daily task today':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Already Completed {task_name} Daily Task Today ]{Style.RESET_ALL}")
                        elif error_my_tasks_complete['message'] == f'Invalid Task: {task_id}':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Invalid Task ID: {task_id} ]{Style.RESET_ALL}")
                        elif error_my_tasks_complete['message'] == 'Task is not completed yet 🐰\nPlease complete and retry!':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ {task_name} Isn\'t Completed Yet. Please Complete And Retry! ]{Style.RESET_ALL}")
                        elif error_my_tasks_complete['message'] == 'Task not found!':
                            return self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ {task_name} Not Found! ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    return self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ {task_name} Completed ]{Style.RESET_ALL}")
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While My Tasks Complete: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While My Tasks Complete: {str(error)} ]{Style.RESET_ALL}")

    async def games_play(self, cookie: str):
        url = 'https://moonrabbits-api.backersby.com/v1/games/play'
        data = json.dumps({'game_type':'FORTUNE_COOKIE'})
        headers = {
            **self.headers,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json',
            'Cookie': cookie
        }
        # while True:
        try:
            async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                    if response.status == 400:
                        error_games_play = await response.json()
                        if error_games_play['message'] == 'No carrots remaining to play the game.':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ No Carrots Remaining To Play The Game ]{Style.RESET_ALL}")
                        elif error_games_play['message'] == 'Invalid access':
                            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Invalid Access While Games Play ]{Style.RESET_ALL}")
                    response.raise_for_status()
                    games_play = await response.json()
                    self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ You\'ve Got {games_play['reward']} From Fortune Cookie ]{Style.RESET_ALL}")
        except ClientResponseError as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Games Play: {str(error)} ]{Style.RESET_ALL}")
        except Exception as error:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Games Play: {str(error)} ]{Style.RESET_ALL}")

    async def main(self, accounts):
        while True:
            try:
                total_balance = 0

                for (cookie, username) in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Tasks ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {username} ]{Style.RESET_ALL}"
                    )
                    await self.my_tasks(cookie=cookie)

                for (cookie, username) in accounts:
                    self.print_timestamp(
                        f"{Fore.WHITE + Style.BRIGHT}[ Mini-games ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}[ {username} ]{Style.RESET_ALL}"
                    )
                    await self.games_play(cookie=cookie)
    
                for (cookie, username) in accounts:
                    my_mrb = await self.my_mrb(cookie=cookie)
                    total_balance += my_mrb['total_mrb'] if my_mrb is not None else 0

                self.print_timestamp(
                    f"{Fore.CYAN + Style.BRIGHT}[ Total Account {len(accounts)} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.GREEN + Style.BRIGHT}[ Total Balance {total_balance} ]{Style.RESET_ALL}"
                )
                self.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ Restarting At {(datetime.now().astimezone() + timedelta(seconds=3600)).strftime('%X %Z')} ]{Style.RESET_ALL}")

                await asyncio.sleep(3600)
                self.clear_terminal()
            except Exception as error:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(error)} ]{Style.RESET_ALL}")
                continue

if __name__ == '__main__':
    try:
        if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        init(autoreset=True)
        moonrabbits = MoonRabbits()

        moonrabbits.print_timestamp(
            f"{Fore.GREEN + Style.BRIGHT}[ 1 ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.BLUE + Style.BRIGHT}[ Generate Tokens ]{Style.RESET_ALL}"
        )
        moonrabbits.print_timestamp(
            f"{Fore.GREEN + Style.BRIGHT}[ 2 ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.BLUE + Style.BRIGHT}[ Load From 'accounts.json' ]{Style.RESET_ALL}"
        )

        initial_choice = int(input(
            f"{Fore.BLUE + Style.BRIGHT}[ {datetime.now().astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.YELLOW + Style.BRIGHT}[ Select Option ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
        ))
        if initial_choice == 1:
            queries = [line.strip() for line in open('queries.txt') if line.strip()]
            if not queries:
                raise FileNotFoundError("Fill Your Query In 'queries.txt'")

            accounts = asyncio.run(moonrabbits.generate_tokens(queries=queries))
            accounts = asyncio.run(moonrabbits.load_from_json())
            open('queries.txt', 'w').close()

            if not accounts:
                raise FileNotFoundError("No accounts found in accounts.json. Please generate tokens first by selecting Option 1.")
        elif initial_choice == 2:
            accounts = asyncio.run(moonrabbits.load_from_json())
            if not accounts:
                raise FileNotFoundError("No Accounts Found In 'accounts.json'. Please Generate Cookie First By Selecting Option 1.")
        else:
            raise ValueError("Invalid Initial Choice. Please Run The Script Again And Choose A Valid Option")

        asyncio.run(moonrabbits.main(accounts))
    except (ValueError, IndexError, FileNotFoundError) as error:
        moonrabbits.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(error)} ]{Style.RESET_ALL}")
    except KeyboardInterrupt:
        sys.exit(0)