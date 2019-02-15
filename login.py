import asyncio
from pyppeteer import launch
from pyppeteer.errors import NetworkError
from datetime import datetime
import os


async def login(customer_info):
    browser = await get_browser(customer_info)
    page = await get_page(browser)
    page = await first_login(page, customer_info)
    return(page)


async def get_browser(customer_info):
    if not os.path.exists(os.path.join('session', customer_info['ticket_id'])):
        os.makedirs(os.path.join('session', customer_info['ticket_id']))

    return await launch(headless=False,
                        userDataDir=os.path.join('session', customer_info['ticket_id']))
    # return await launch()


async def get_page(browser):
    page = await browser.newPage()
    await page.goto("https://en.eztable.com/")
    return page


async def first_login(page, customer_info):
    # Click member icon to show login pop-up
    await page.waitForSelector('.header-member')
    await page.click('.header-member')
    await page.waitFor(2000)

    # Fill in phone number and click "Next"
    await page.type('#tel-input-header', customer_info['phone_number'])
    element = await page.Jx(
        '//div[@class="login-form"]//div[@class="btn border-btn primary-btn"]')
    element = element[0]
    await element.click()

    # Wait for SMS verification code and fill in
    await page.waitForXPath('//div[@class="login-form"]//input[@type="tel"]')
    ver_code = input('The code has been send to your phone via SMS.\n'
                     'Please enter the code received: ')
    element = await page.Jx('//div[@class="login-form"]//input[@type="tel"]')
    element = element[0]
    await element.type(ver_code)

    # Click verify.
    element = await page.Jx(
        '//div[@class="login-form"]//div[@class="btn border-btn primary-btn"]')
    element = element[0]
    await element.click()

    return(page)

if __name__ == "__main__":
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
            page = loop.run_until_complete(login(customer_info))
            connected = True
        except NetworkError:
            print("Time out...")
            pass
