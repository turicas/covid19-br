import argparse
import shutil
import time

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from splinter import Browser
from splinter.driver.webdriver import BaseWebDriver, WebDriverElement


def get_chrome(lang=None, width=None, height=None):
    if lang is not None:
        options = Options()
        options.add_experimental_option("prefs", {"intl.accept_languages": lang})
        browser = BaseWebDriver()
        browser.element_class = WebDriverElement
        browser.driver = Chrome(options=options)
    else:
        browser = Browser("chrome")

    if width is not None and height is not None:
        browser.driver.set_window_size(width, height)

    return browser


def take_element_screenshot(url, element_xpath, lang=None, wait=None, width=None, height=None):
    browser = get_chrome(lang=lang, width=width, height=height)
    browser.visit(url)
    if wait:
        time.sleep(wait)
    element = browser.find_by_xpath(element_xpath).first
    filename = element.screenshot(full=True)
    browser.quit()
    return filename


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()

    url = "https://datastudio.google.com/u/0/reporting/5f774971-ab0f-4b89-af6f-0014332c3e84/page/YbETB"
    element_xpath = "//div[@class='reportArea']"
    width = 1600
    height = 1600

    filename = take_element_screenshot(
        url,
        element_xpath,
        lang="pt-BR",
        wait=3,
        width=width,
        height=height,
    )
    shutil.move(filename, args.filename)
