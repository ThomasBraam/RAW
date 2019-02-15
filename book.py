import asyncio
import re
from pyppeteer import launch
from pyppeteer.errors import NetworkError
from datetime import datetime
import os


async def book(ticket_info):
    browser = await get_browser()
    page = await get_page(browser)
    page, chosen_ticket = await find_and_select_day(page, ticket_info)
    page = await make_reservation(page, customer_info)
    return(page)


async def get_browser():
    browser = await launch(headless=False,
                           userDataDir=os.path.join('session', customer_info['ticket_id']))
    # browser = await launch(userDataDir=os.path.join('session', customer_info['ticket_id']))
    return browser


async def get_page(browser):
    page = await browser.newPage()
    await page.goto("https://wv.eztable.com/widget/raw?locale=en_US")
    return page


async def find_and_select_day(page, ticket_info):
    await page.waitForSelector('#widget > main > div >div.selector-wrapper > \
                                label > select')

    # Select amount of people
    await page.select('#widget > main > div > div.selector-wrapper > label > \
                       select', ticket_info['people'])

    # Select day
    ticket_date = datetime.strptime("{Y} {B} {d}".format(Y=ticket_info['year'],
                                                         B=ticket_info['month'],
                                                         d=ticket_info['day']),
                                    "%Y %B %d")
    ticket_date_string = ticket_date.strftime('%A, %B %-d, %Y')
    element = []
    await page.waitFor(1000)
    while not element:
        element = await page.Jx(
            '//button[@aria-label="{}"]'.format(ticket_date_string))
        if element:
            continue
        element_next_month = await page.Jx(
            '//button[@aria-label="Move forward to switch to the next month."]')
        await element_next_month[0].click()
        await page.waitFor(1000)
    await element[0].click()

    # Create time and prices list.
    await page.waitForSelector('.quota-group')
    element_dict = {}
    elements = await page.Jx('//div[@class="quota-group"]')
    if not elements:
        raise ValueError('No times available.')

    for i in range(1, len(elements) + 1):
        element = await page.Jx(
            '//div[@class="quota-group"][{}]'.format(i))
        element = await element[0].getProperty('textContent')  # Get price
        price = await element.jsonValue()
        price = int(re.findall(r'\d+,\d+', price)[0].replace(',', ''))

        element = await page.Jx(
            '//div[@class="quota-group"][{}]//li[@class="quota"]'.format(i))
        element_dict[price] = {}
        for j in range(len(element)):
            time = await element[j].getProperty('textContent')  # Get time
            time = await time.jsonValue()
            element_dict[price][time] = (i, j)

    # Choose ticket that is within price range and highest ranked in time.
    chosen_ticket = {}
    for price in sorted(element_dict.keys()):
        if price > ticket_info['min_price'] and price < ticket_info['max_price']:
            for time in ticket_info['time']:
                if time in element_dict[price].keys():
                    chosen_ticket['time'] = time
                    chosen_ticket['price'] = price
                    chosen_ticket['id'] = element_dict[price][time]
    if not chosen_ticket:
        raise ValueError(
            'Could not find appropriate ticket,'
            ' probably no seats available within price range.')

    # Select that ticket
    element = await page.Jx(
        '//div[@class="quota-group"][{}]//li[@class="quota"][{}]'.format(
            chosen_ticket['id'][0],
            chosen_ticket['id'][1],))
    element = element[0]
    await element.click()

    # Click 'I Agree' and 'Confirm'
    await page.waitForSelector('#jamie-checkbox')
    await page.click('#jamie-checkbox')

    element = await page.Jx(
        '//div[@class="hanlai-popup jamie-popup"]//div[@class="button active"]')
    await element[0].click()

    return(page, chosen_ticket)


async def make_reservation(page, customer_info):
    #### First page, customer info
    # Input name
    await page.waitForSelector('.input-group')
    element = await page.Jx('//div[@class="name-input-wrapper"]//input[@class="input"]')
    await element[0].type(customer_info['name'])

    # Input email
    element = await page.Jx('//div[@class="input-group"][3]//input[@class="input"]')
    await element[0].type(customer_info['email'])

    # Click 'Next'
    element = await page.Jx('//div[@class="btn footer-btn secondary-btn"]')
    await element[0].click()

    #### Second page
    # Click 'Next'
    await page.waitForXPath('//div[@class="btn footer-btn secondary-btn"]')
    element = await page.Jx('//div[@class="btn footer-btn secondary-btn"]')
    await element[0].click()

    #### Third page, credit card info
    # Input credit card number
    await page.waitForSelector('.ccNumber')
    await page.type('.ccNumber', customer_info['CC_no'])

    # Input credit card expiry date
    await page.type('.ccExpiry', customer_info['CC_exp'])

    # Input credit card CVC
    await page.type('.ccCVC', customer_info['CC_CVC'])

    # Click 'Next'
    element = await page.Jx('//div[@class="btn footer-btn secondary-btn"]')
    await element[0].click()

    # Click 'Confirm'    
    await page.waitForXPath('//div[@class="btn secondary-btn"]')
    element = await page.Jx('//div[@class="btn secondary-btn"]')
    # await element[0].click()

    return(page)


if __name__ == "__main__":
    ticket_info = {
        'year': '2019',
        'month': 'April',
        'day': '4',
        'time': ['18:15', '18:00', '18:30', '18:45', '19:00',
                 '19:15', '19:30', '19:45', '20:00'],
        'people': '4',
        'min_price': 2000,
        'max_price': 3000}

    customer_info = {
        'ticket_id': '01',
        'phone_number': '0912345678',
        'name': 'BB King',
        'email': 'BBKing@gmail.com',
        'CC_no': '1337133713371337',
        'CC_exp': '0219',
        'CC_CVC': '555',
    }

    loop = asyncio.get_event_loop()

    connected = False
    while not connected:
        try:
            page = loop.run_until_complete(book(ticket_info))
            connected = True
        except NetworkError:
            print("Time out...")
            pass
