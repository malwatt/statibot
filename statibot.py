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
MAX_LIKES = 1000
MAX_LIKED_SCREENS = 3


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


def delay():
    """Generate random sleep time to make navigating and clicking more human."""
    return random.uniform(1.0, 1.5)


def process_account(driver, wait, account):
    """For account, search for each hashtag, select the exact match, and like
    unliked pics up to the likes count for each hashtag."""
    username_password = account[0]
    hashtags_likes = account[1:]

    # Click login button.
    login_button = wait.until(lambda s: s.find_element(
        By.XPATH, '//*[@id="content"]/header[1]/div/a[2]'))
    time.sleep(delay())
    login_button.click()

    # Enter username.
    username = wait.until(lambda s: s.find_element(
        By.XPATH, '//*[@id="id_username"]'))
    time.sleep(delay())
    username.send_keys(username_password[0])

    # Enter password and login.
    password = wait.until(lambda s: s.find_element(
        By.XPATH, '//*[@id="id_password"]'))
    time.sleep(delay())
    password.send_keys(username_password[1])
    password.send_keys(Keys.RETURN)

    # Find hashtag search field.
    search = wait.until(lambda s: s.find_elements(
        By.XPATH, '//*[@id="getSearch"]'))[1]

    for hashtag, likes in hashtags_likes:
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
            print '  Hashtag "%s" - Not Found.' % hashtag
            continue

        time.sleep(delay())
        tag.click()

        print '  Hashtag "%s" %d...' % (hashtag, likes)

        # Like unliked pics for this hashtag, extending the screen as required.
        screen = 0
        screen_tries = 0
        count = 0
        failed = 0
        end_of_page = False
        shortwait = WebDriverWait(driver, 5)
        while count < likes and count < MAX_LIKES:
            screen += 1

            # Get unliked pics on screen.
            try:
                unlikeds = wait.until(lambda s: s.find_elements(
                    By.XPATH, '//*[@class="photos-wrapper"]/div/a[@class="like_picto_unselected likeAction ss-heart"]'))
            except:
                unlikeds = []
            todo = len(unlikeds)

            if unlikeds:
                screen_tries = 0
                # Get liked pics on screen.
                try:
                    likeds = wait.until(lambda s: s.find_elements(
                        By.XPATH, '//*[@class="photos-wrapper"]/div/a[@class="like_picto_selected unlikeAction ss-heart"]'))
                except:
                    likeds = []
                already = len(likeds)

                # Like the unliked pics on screen.
                for unliked in unlikeds:
                    time.sleep(delay() * 10)
                    unliked.click()

                # Get unliked pics now on screen.
                try:
                    unlikeds2 = wait.until(lambda s: s.find_elements(
                        By.XPATH, '//*[@class="photos-wrapper"]/div/a[@class="like_picto_unselected likeAction ss-heart"]'))
                except:
                    unlikeds2 = []
                failed = len(unlikeds2)

                done = todo - failed
                count += done

                print '    Screen %00d Attempted %00d Liked %00d Total %00d.' \
                    % (screen, todo, done, count)

            # Extend screen.
            try:
                # Firefox will scroll down and use this to extend page.
                more = wait.until(lambda s: s.find_element(
                    By.XPATH, '//*[@id="conteneur-more"]/a'))
                time.sleep(delay())
                more.click()
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

            # Statigram clicks usually go awry after traversing several fully
            # or mostly liked screens. Quitting while ahead.
            screen_tries += 1
            if screen_tries >= MAX_LIKED_SCREENS:
                break

        print '  Hashtag "%s" - Liked %d/%d.' % (hashtag, count, likes)
        if failed:
            print '    Encountered Statigram click errors.'
        elif screen_tries >= MAX_LIKED_SCREENS:
            print '    Reached already liked screens.'
        elif count >= likes:
            print '    Reached set likes count.'
        elif count >= MAX_LIKES:
            print '    Reached maximum allowed likes.'
        else:
            print '    Reached end of page.'

        # Scroll back to top to be ready to use search field again.
        driver.execute_script("window.scrollTo(0, 0);")

    return True


def main():
    argvs = sys.argv[1:]
    try:
        accounts = get_accounts(argvs)
    except:
        return

    driver = get_webdriver()
    if not driver:
        return

    wait = WebDriverWait(driver, 10)

    for account in accounts:
        print '\nAccount "%s"...' % account[0][0]
        processed = process_account(driver, wait, account)
        if processed:
            print 'Account "%s" OK.' % account[0][0]
        else:
            print 'Account "%s" Error.' % account[0][0]

    #return  # To stay logged in and leave browser open.

    # Scroll back to top and logout.
    driver.execute_script("window.scrollTo(0, 0);")
    logout_button = wait.until(lambda s: s.find_element(By.ID, 'avatar'))
    time.sleep(delay())
    logout_button.click()
    logout_option = wait.until(lambda s: s.find_element(
        By.XPATH, '//*[@id="ui-tooltip-0-content"]/a[@href="/?action=logout"]'))
    time.sleep(delay())
    logout_option.click()

    # Close browser window.
    time.sleep(delay())
    driver.delete_all_cookies()
    driver.quit()


if __name__ == '__main__':
    main()
