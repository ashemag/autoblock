import urllib.request
import selenium
from selenium import webdriver
from bs4 import BeautifulSoup
import requests
import re
import json
import time
import os
import chromedriver_autoinstaller
import stdiomask


class Blocker:
    def __init__(self):
        self.driver = self.setup_driver()
        self._twitter_login()

    def run(self):
        self._block()
        print("Done!")
        print("https://twitter.com/settings/blocked/all")

    def setup_driver(self):
        # autoinstall chrome driver
        chromedriver_autoinstaller.install(cwd=True)
        folder = [item for item in os.listdir() if '8' in item][0]

        # set bot options
        options = webdriver.ChromeOptions()
        options.add_argument("--user-data-dir=chrome-data")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("start-maximized")
        options.add_argument("--window-size=400,768")

        driver = webdriver.Chrome(options=options, executable_path=f"{folder}/chromedriver")
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        driver.execute_cdp_cmd(
            'Network.setUserAgentOverride',
            {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'
            },
        )
        print(driver.execute_script("return navigator.userAgent;"))

        return driver

    def _twitter_login(self):
        self.driver.get('https://twitter.com/login')
        time.sleep(5)
        if 'Home' in self.driver.title:
            print("Already logged in!")
        else:
            username, password = self._prompt_user_login()

            self.driver.find_element_by_xpath("//input[contains(@name,'username')]").send_keys(
                username
            )
            self.driver.find_element_by_xpath("//input[contains(@name,'password')]").send_keys(
                password
            )
            self.driver.find_elements_by_xpath("//*[contains(text(), 'Log in')]")[1].click()

    def _block(self):
        path = self._prompt_user_hateful_tweet()
        hateful_users = self._fetch_users_to_block(path)
        for u in hateful_users:
            print(f"Blocking {u}")
            self._block_user(u)

        self.driver.quit()

    def _fetch_users_to_block(self, path):
        if "likes" not in path:
            path = os.path.join(path, "likes")

        self.driver.get(path)
        usernames = set()
        hateful_user = '@' + path.split('/')[3]
        usernames.add(hateful_user)
        scroll_height = 0
        window = 400
        no_change = 0

        while no_change < 3:
            scroll_height += window
            self.driver.execute_script(f"window.scrollTo(0, {scroll_height})")
            time.sleep(5)
            el = self.driver.find_element_by_tag_name('body')
            prev_num = len(usernames)
            for item in el.text.split('Follow'):
                if '@' in item:
                    username = '@' + item.split('@')[-1].split('\n')[0]
                    usernames.add(username)
                    count += 1

            # check if user name is the same value as its prev. if yes increment no change marker
            if len(usernames) == prev_num:
                no_change += 1
            else:
                no_change = 0

        print(f"{len(usernames)} users extracted...")
        return usernames

    def _block_user(self, username):
        try:
            username = username.replace('@', '')
            self.driver.get(f'https://twitter.com/{username}')
            time.sleep(2)
            self.driver.find_elements_by_css_selector("svg")[12].click()
            time.sleep(2)
            self.driver.find_elements_by_xpath("//*[contains(text(), 'Block')]")[0].click()
            time.sleep(2)
            self.driver.find_elements_by_xpath("//*[contains(text(), 'Block')]")[1].click()
            time.sleep(2)
        except Exception as e:
            print(e)
            print(f"Failed...user {username} is most likely already blocked")

    def _prompt_user_login(self):
        line_1 = "Terminal will ask you a few questions."
        line_2 = "If your username and/or password are saved as environment variables, simply press enter for those prompts."
        line_3 = "Happy blocking (:"
        instructions = f"""---\n\n{line_1}\n{line_2}\n{line_3}\n\n---\n"""
        print(instructions)

        username = input("Enter in your twitter username: ")
        if not username:
            username = os.getenv("TWITTER_USERNAME")

        password = stdiomask.getpass("Enter your twitter password: ")

        if not password:
            password = os.getenv("TWITTER_PASSWORD")

        return username, password

    def _invalid_hateful_tweet(self, tweet_link):
        if 'https' not in tweet_link:
            return True
        if 'twitter' not in tweet_link:
            return True
        if 'status' not in tweet_link:
            return True

        return False

    def _prompt_user_hateful_tweet(self):
        print("A sample tweet format is https://twitter.com/<username>/status/<status>")
        hateful_tweet_link = input("Enter in the hateful tweet link: ").lower()
        if self._invalid_hateful_tweet(hateful_tweet_link):
            raise ValueError("Please pass in a valid tweet link.")
        return hateful_tweet_link