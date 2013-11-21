#!/usr/bin/env python

import os
import sys
import random
import time

from glob import glob
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


WEBDRIVER = 'Firefox'  # 'Firefox' 'Chrome' 'PhantomJS'
ACCOUNTS_FILE = 'accounts.txt'
MAX_LIKES = 200
MAX_LIKED_SCREENS = 2
SKIP = 2
SECONDS_MIN = 0.5
SECONDS_MAX = 2.0


def get_webdriver():
    """Set up WebDriver."""
    # Firefox the most stable.
    if WEBDRIVER == 'Firefox':
        # Crashes if Flash installed. Otherwise most consistent.
        profile = webdriver.FirefoxProfile(
            "C:\\Users\Malky\\AppData\\Local\\Mozilla\\Firefox\\Profiles\\cxah9ogf.Selenium")
        driver = webdriver.Firefox(profile)
    elif WEBDRIVER == 'Chrome':
        # Crashes too often when scrolling.
        driver = webdriver.Chrome(executable_path=
            "C:\\Program Files (x86)\\chromedriver_win32\\chromedriver.exe")
    elif WEBDRIVER == 'PhantomJS':
        # Doesn't even get to 1st base.
        driver = webdriver.PhantomJS(
            "C:\\Program Files (x86)\\phantomjs-1.9.2-windows\\phantomjs.exe")
    else:
        print 'No WebDriver specified.'
        return False

    driver.delete_all_cookies()
    driver.get("http://statigr.am/")
    driver.maximize_window()

    return driver


def get_account(line, elements):
    """Get account username, password, and hashtags and likes counts."""
    if len(elements) < 4:
        if line:
            print 'Insufficient Instagram account info in line %d of file "%s"!\n \
For each account, put a space-separated line with:\n \
e.g. username password hashtag1 1000 [hashtag2 500] ...' \
% (line, accounts_file.split('/')[-1])
        else:
            print 'Insufficient Instagram account info entered!\n \
Space-separated arguments required:\n \
e.g. username password hashtag1 1000 [hashtag2 500] ...'
        return False

    if len(elements) % 2:
        if line:
            print 'Mismatched account info in line %d of file "%s"!\n \
For each account, put a space-separated line with:\n \
e.g. username password hashtag1 1000 [hashtag2 500] ...' \
% (line, accounts_file.split('/')[-1])
        else:
            print 'Mismatched account info entered!\n \
Space-separated arguments required:\n \
e.g. username password hashtag1 1000 [hashtag2 500] ...'
        return False

    username = elements[0]
    password = elements[1]

    account = [[username, password,],]
    for i, element in enumerate(elements[2:]):
        if i % 2 == 0:
            hashless = element.strip("#")
            if hashless.isalnum():
                l = [hashless,]
            else:
                if line:
                    print 'Mismatched hashtags and likes in line %d of file "%s"!\n \
Please give a list of hashtags and number of likes for each.\n \
e.g. hashtag1 1000 hashtag2 500 ...' \
% (line, accounts_file.split('/')[-1])
                else:
                    print 'Mismatched hashtags and likes entered!\n \
Please give a list of hashtags and number of likes for each.\n \
e.g. hashtag1 1000 hashtag2 500 ...'
                return False
        else:
            if element.isdigit():
                l.append(int(element))
                account.append(l)
            else:
                if line:
                    print 'Mismatched hashtags and likes in line %d of file "%s"!\n \
Please give a list of hashtags and number of likes for each.\n \
e.g. hashtag1 1000 hashtag2 500 ...' \
% (line, accounts_file.split('/')[-1])
                else:
                    print 'Mismatched hashtags and likes entered!\n \
Please give a list of hashtags and number of likes for each.\n \
e.g. hashtag1 1000 hashtag2 500 ...'
                return False

    return account


def get_accounts(argvs):
    """Get list of accounts, i.e. their username, password, and hashtags and
    likes counts from ACCOUNTS_FILE, or an account from command-line arguments.
    """
    current_path = os.path.abspath(
        os.path.dirname(__file__).decode('utf-8')).replace('\\','/')
    accounts = []

    if argvs:
        try:
            accounts.append(get_account(0, argvs))
        except:
            return False
    else:
        try:
            accounts_file = glob(os.path.join(current_path, ACCOUNTS_FILE))[0]
        except:
            print 'Instagram accounts file "%s" not found.' % ACCOUNTS_FILE
            return False

        try:
            with open(accounts_file, 'rb') as in_f:
                lines = [line.strip() for line in in_f.readlines()]
            in_f.close()
        except:
            print 'Problem reading Instagram accounts file "%s".' \
                % accounts_file.split('/')[-1]
            return False

        if not len(lines):
            print 'No Instagram accounts given in file "%s"!\n \
For each account, put a space-separated line with:\n \
e.g. username password hashtag1 1000 [hashtag2 500] ...' \
% accounts_file.split('/')[-1]
            return False

        for i, line in enumerate(lines):
            elements = line.split()

            try:
                accounts.append(get_account(i + 1, elements))
            except:
                return False

    return accounts


def process_account(account):
    """For each hashtag in account, login, search for hashtag, select the exact
    match, like unliked pics up to the likes count for each hashtag, then
    logout."""

    hashtags_likes = account[1:]

    for hashtag, likes in hashtags_likes:
        print '  Hashtag "%s" %d...' % (hashtag, likes)

        # Safest to start a new session for each hashtag.
        try:
            driver, wait = login(account)
        except:
            return False

        # Find hashtag search field.
        try:
            search = wait.until(lambda s: s.find_elements(
                By.XPATH, '//*[@id="getSearch"]'))[1]
        except:
            print '    Could not find search field.' % hashtag
            return False

        # Search for hashtag.
        time.sleep(delay())
        search.clear()
        search.send_keys(hashtag)
        search.send_keys(Keys.RETURN)

        # Select first matching hashtag.
        try:
            tag = wait.until(lambda s: s.find_element(
                By.XPATH, '//*[@id="resultatSearchTag"]/ul/li[1]/a'))
        except:
            print '    Hashtag "%s" - Not Found.' % hashtag
            if not logout(driver, wait):
                return False
            continue
        time.sleep(delay())
        tag.click()

        # Set pause points at a random click count interval for this hashtag.
        pause = random.randint(15, 25)
        print '    Set to pause every %d clicks.' % pause

        # Set pic click points at a random click count interval for this hashtag.
        pic_click = random.randint(15, 25)
        print '    Set to open a pic every %d clicks.' % pic_click

        # Like unliked pics for this hashtag, extending the screen as required.
        screen = 0
        screen_tries = 0
        clicks = 0
        count = 0
        end_of_page = False
        while count < likes and count < MAX_LIKES:
            screen += 1
            failed = 0

            # Get unliked pics on screen.
            try:
                unlikeds = wait.until(lambda s: s.find_elements(
                    By.XPATH, '//*[@class="photos-wrapper"]/div/a[@class="like_picto_unselected likeAction ss-heart"]'))
            except:
                unlikeds = []

            # Skip liking a certain number per screen.
            todo = len(unlikeds) - SKIP * screen
            print '    Screen %00d To Do %d.' % (screen, todo)

            if todo > 0:
                screen_tries = 0

                # Ignore skipped items of previous screens.
                for i in xrange(SKIP * (screen - 1)):
                    unlikeds.pop(0)
                print '    Popped first %d unliked elements on total page.' % (SKIP * (screen - 1) + 1)
                print '    Screen %00d Total Unliked %d.' % (screen, len(unlikeds))

                # Set random indices of pics to skip liking on this screen.
                skips = random.sample(xrange(len(unlikeds)), SKIP)
                print '    Set to skip indices %s.' % sorted(skips)

                # Get liked pics on screen.
                try:
                    likeds = wait.until(lambda s: s.find_elements(
                        By.XPATH, '//*[@class="photos-wrapper"]/div/a[@class="like_picto_selected unlikeAction ss-heart"]'))
                except:
                    likeds = []
                already = len(likeds)

                # Like the unliked pics on screen, minus the ones to skip.
                for i, unliked in enumerate(unlikeds):
                    if i in skips:
                        print '    Skipped index %d.' % i
                        continue

                    clicks += 1
                    print '    Click %d.' % clicks

                    # Random pic click, then return and continue.
                    # Is back button disrupting flow?
                    #if not clicks % pic_click:
                    #    print 'pic clicking'
                    #    current = unliked
                    #    pic = current.find_element_by_xpath(
                    #        '../../div/a[@class="lienPhotoGrid"]')
                    #    time.sleep(delay() * 10)
                    #    pic.click()
                    #    time.sleep(delay() * 10)
                    #    driver.back()

                    # Random pause.
                    if not clicks % pause:
                        print '    Click %d Pausing.' % clicks
                        time.sleep(delay() * 100)

                    time.sleep(delay() * 10)
                    unliked.click()

                    # Check if liked ok by trying to find the unliked element.
                    current = unliked
                    time.sleep(delay())
                    try:
                        check = current.find_element_by_xpath(
                            '../a[@class="like_picto_unselected likeAction ss-heart"]')
                    except:
                        pass
                    else:
                        failed += 1

                # Get unliked pics now on screen.
                #try:
                #    unlikeds2 = wait.until(lambda s: s.find_elements(
                #        By.XPATH, '//*[@class="photos-wrapper"]/div/a[@class="like_picto_unselected likeAction ss-heart"]'))
                #except:
                #    unlikeds2 = []
                #failed = len(unlikeds2) - SKIP * screen

                done = todo - failed
                count += done

                print '    Screen %00d Attempted %00d Liked %00d Total %00d.' \
                    % (screen, todo, done, count)

            # Extend screen.
            try:
                # Firefox will scroll down and use this to extend page.
                more = wait.until(lambda s: s.find_element(
                    By.XPATH, '//*[@id="conteneur-more"]/a'))
            except:
                if WEBDRIVER == 'Chrome':
                    # Chrome won't find the above if it isn't already visible.
                    # It must be scrolled manually, but sometimes crashes.
                    # Also lose functionality below.
                    driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);")
                else:
                    # Using the exception here to catch end of entire page.
                    end_of_page = True
                    break
            else:
                time.sleep(delay())
                more.click()

            # Statigram clicks usually go awry after traversing several fully
            # or mostly liked screens. Quitting while ahead.
            screen_tries += 1
            if screen_tries >= MAX_LIKED_SCREENS:
                break

        print '  Hashtag "%s" - Liked %d/%d.' % (hashtag, count, likes)
        if failed:
            print '  Encountered Statigram click errors.'
        elif screen_tries >= MAX_LIKED_SCREENS:
            print '  Reached already liked screens.'
        elif count >= likes:
            print '  Reached set likes count.'
        elif count >= MAX_LIKES:
            print '  Reached maximum allowed likes.'
        else:
            print '  Reached end of page.'

        if not logout(driver, wait):
            return False
        time.sleep(delay() * 1000)

    return True


def login(account):
    """Login to Instagram account."""
    username_password = account[0]

    driver = get_webdriver()
    if not driver:
        return False

    wait = WebDriverWait(driver, 10)

    # Click login button.
    try:
        login_button = wait.until(lambda s: s.find_element(
            By.XPATH, '//*[@id="content"]/header[1]/div/a[2]'))
    except:
        print '    Could not find login button.'
        return False
    time.sleep(delay())
    login_button.click()

    # Enter username.
    try:
        username = wait.until(lambda s: s.find_element(
            By.XPATH, '//*[@id="id_username"]'))
    except:
        print '    Could not find username field.'
        return False
    time.sleep(delay())
    username.send_keys(username_password[0])

    # Enter password and login.
    try:
        password = wait.until(lambda s: s.find_element(
            By.XPATH, '//*[@id="id_password"]'))
    except:
        print '    Could not find password field.'
        return False
    time.sleep(delay())
    password.send_keys(username_password[1])
    password.send_keys(Keys.RETURN)

    # Check for login button reappearing, meaning login failed.
    try:
        login_button_check = wait.until(lambda s: s.find_element(
            By.XPATH, '//*[@id="content"]/header[1]/div/a[2]'))
    except:
        pass
    else:
        print '    Could not login.'
        return False

    return (driver, wait)


def logout(driver, wait):
    """Logout of Instagram account."""

    # Scroll to top of screen.
    driver.execute_script("window.scrollTo(0, 0);")

    try:
        logout_button = wait.until(lambda s: s.find_element(By.ID, 'avatar'))
    except:
        print '    Could not find logout button.'
        return False
    time.sleep(delay())
    logout_button.click()

    try:
        logout_option = wait.until(lambda s: s.find_element(
            By.XPATH, '//*[@id="ui-tooltip-0-content"]/a[@href="/?action=logout"]'))
    except:
        print '    Could not find logout option.'
        return False
    time.sleep(delay())
    logout_option.click()

    # Close browser window.
    time.sleep(delay())
    driver.delete_all_cookies()
    driver.quit()

    return True


def delay():
    """Generate random sleep time to make navigating and clicking more human."""
    return random.uniform(SECONDS_MIN, SECONDS_MAX)


def main():
    argvs = sys.argv[1:]
    try:
        accounts = get_accounts(argvs)
    except:
        return

    for account in accounts:
        print '\nAccount "%s"...' % account[0][0]
        processed = process_account(account)
        if processed:
            print 'Account "%s" OK.' % account[0][0]
        else:
            print 'Account "%s" Error.' % account[0][0]


if __name__ == '__main__':
    main()
