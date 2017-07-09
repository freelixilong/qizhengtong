# code: UTF-8
import re
import logging
import six
import copy
import json
import re
#import scrapy,random
#from scrapy.utils.sitemap import Sitemap, sitemap_urls_from_robots
#from scrapy.spiders import Spider
#from scrapy.http import Request, XmlResponse
#from scrapy.utils.sitemap import Sitemap, sitemap_urls_from_robots
from scrapy.utils.gz import gunzip, is_gzipped
from scrapy.linkextractors import LinkExtractor
from scrapy.utils.python import unique as unique_list
from scrapy.exceptions import NotSupported
#from scrapy_splash import SplashRequest
#from MySpider.lua import proxyServer
#from MySpider.agent import agents
from scrapy.http.response.text import TextResponse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from . import BaseSpider
import pdb
from logger import getLogger
from selenium.common.exceptions import ElementNotVisibleException

#proxyProc = proxyServer()
logger = getLogger()

class CommSpider(BaseSpider):
    name = "GovSpider"

    #def __init__(self, deny = '', filter_urls = [], condition = "", title = '', content = "",
    #    date = "", *a, **kw):
    def __init__(self, browser ,settings, *a, **kw):
        super(CommSpider, self).__init__(browser ,settings, *a, **kw)

    def start_once(self, site= None, startUrl = None):
        """mainly for test """
        res = self.db.GovDepartment.find_one({"key": site})
        self._init_gov_data(res)
        logger.info('start oncec crawl %s!'%startUrl)
        #self.start_requests()
        self.request(startUrl)
        self.destroy_init_data()

    def link_extract(self):
        self.link_extractor = LinkExtractor(allow=[self.start_host], deny=(), allow_domains=(), deny_domains=(), restrict_xpaths=(),
                 tags=('a', 'area'), attrs=('href',), canonicalize=True, unique=True, process_value=None, deny_extensions=None, restrict_css=())

    def noError(self, browser):
        try:
            res = re.search("(\.\.\/){4,}", self.currentUrl)
            if not res is None:
                return False
            t = browser.find_element_by_xpath("/html/body/pre").text
            dic = json.loads(t)
            ex = dic["error"]

            if ex == 502 or ex == 404 or ex == 500:
                return False
        except Exception, e:
            return True
        return True

    def request(self, url):
        try:
            #logger.info("start crawl url: %s"%url)
            self._getPage(url, self.browser)
            logger.info("crawled url: %s"%url)
            self.crawedAppend(url)
            if self.noError(self.browser):
                res = self.getResponse(url, self.browser)
                site_urls = self.link_extractor.extract_links(res)
                site_urls = self.add_urls_noduplicate(site_urls)
                if self.satisfy_craw(res):
                    item =  self.get_item(res)
                    self.save_item(item)
                nextXpath = self.get_next_page_xpath(self.browser)

                if nextXpath:
                    self.craw_next_pages(nextXpath, site_urls)
                for url in site_urls:
                    if not self.hasCrawedUrl(url):
                        self.request(url) ##once come here, the browser is dirty data
        except Exception as e:
            logger.warning('exceptions happended %s'%e.message)
        else:
            return
    def get_next_page_xpath(self, browser):
        return False

class NextPageActionSpider(CommSpider):
        nextPages = []
        def _init_gov_data(self, gov):
            super(NextPageActionSpider, self)._init_gov_data(gov)
            if not gov["nextPageXpath"] is None:
                if type(gov["nextPageXpath"])==str or type(gov["nextPageXpath"])==unicode:
                    self.nextPages.append(gov["nextPageXpath"])
                else:
                    for nextPage in gov["nextPageXpath"]:
                        self.nextPages.append(nextPage)
        def destroy_init_data(self):
            super(NextPageActionSpider, self).destroy_init_data()
            self.nextPages = []

        def craw_next_pages(self, nextXpath, dstArr):
            class wait_for_next_element(object):
                def __init__(self, xpath):
                    #self.locator = locator
                    self.xpath = xpath
                def __call__(self, driver):
                    #elements = [element for element in EC._find_elements(driver, self.locator) if EC.element_to_be_clickable(element)]
                    try:
                        elements = driver.find_element_by_xpath(self.xpath)
                        for elment in elements:
                            if EC.element_to_be_clickable(element):
                                return True
                        return False
                    except Exception as e:
                        logger.warning("when travel next page error haapend %s"%e.message)
            try:
                tempBrowser = webdriver.Firefox()

                while self.browser.find_element_by_xpath(nextXpath):
                    res =self.getResponse(self.currentUrl, self.browser)
                    self.crawedAppend(self.currentUrl)
                    site_urls = self.link_extractor.extract_links(res)
                    site_urls = self.add_urls_noduplicate(site_urls)
                    for url in site_urls:
                        self._getPage(url, tempBrowser)
                        if self.noError(self, tempBrowser):
                            logger.info("crawled n url: %s"%url)
                            #self.crawedAppend(url)
                            res =self.getResponse(url, tempBrowser)
                            self.browser
                            if self.satisfy_craw(res):
                                self.crawedAppend(url)
                                item =  self.get_item(res)
                                self.save_item(item)
                            else:
                                self._add_url_nodup(url, dstArr)

                    self.browser.find_element_by_xpath(nextXpath).click()
                    #nextElement = wait_for_next_element(nextXpath)
                    WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.XPATH, nextXpath)))

            except Exception as e:
                logger.warning('craw_next_pages failed %s'%e.message)
                logger.warning('craw_next_pages may not have next page any more!')
            finally:
                tempBrowser.close()

        def get_next_page_xpath(self, browser):
            for nextPage in self.nextPages:
                try:
                    if browser.find_element_by_xpath(nextPage):
                        return nextPage
                except Exception as e:
                    return None
            return None


class ActionSpider(CommSpider):
    """for http://www.ccgp-hebei.gov.cn, this site's all href is linked by clicked
    not by location"""
    def __init__(self, browser ,settings, *a, **kw):
        super(ActionSpider, self).__init__(browser ,settings, *a, **kw)
        self.current_window_handle = None
        self.tabsQueue = []

    def _getPage(self, url, browser):
        print "get nUrl %s"%url
        self.currentUrl = url
        browser.get(url)

    def request(self, url):
        self._getPage(url, self.browser)
        try:
            #tempBrowser = webdriver.Firefox()
            if (not self.hasCrawedUrl(url)):
                logger.info("crawled url: %s"%url)
                self.crawedAppend(url)
                res = self.getResponse(url, self.browser)

                if self.satisfy_craw(res):
                    self.extract_page_content(res)
                else:
                    self.craw_sub_page(self.browser)

        except Exception as e:
            logger.warning('Action spider request failed %s'%e.message)
            logger.warning('sub page may not have page anymore!')

    def extract_page_content(self, res):
        item =  self.get_item(res)
        self.save_item(item)
    def get_page_links(self, browser, i):
        pdb.set_trace()
        if i != 0:
            browser.back()
            sleep(1)
            aElements = browser.find_elements_by_tag_name("a")
            count = 0
            if aElements != None:
                for element in aElements:
                    try:
                        count += 1
                        if count == i:
                            element.click()
                            WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                            import pdb; pdb.set_trace()
                            sleep(1)
                            return browser.current_url
                    except ElementNotVisibleException as e:

                        print("not visible message %s"%e.message)
                    except Exception as e:
                        print("error message %s"%e.message)
                        pdb.set_trace()
                        return ""

                return ""

        else:
            element = browser.find_element_by_tag_name("a")
            if element != None:
                try:
                    element.click()
                    #sleep(3)
                    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    return browser.current_url
                except Exception as e:
                    print("the first click link error message %s"%e.message)

            else:
                return ""

    def craw_sub_page(self, browser):
        aElements = browser.find_elements_by_tag_name("a")
        links = []
        count = 0
        elen = len(aElements)

        for i in range(elen):
            url = self.get_page_links(browser, i)
            if (url != "") and not( url in links):
                print("get link %s"%url)
                links.append(url)

        print("travels tabs")
        for link in links:
            print ("current link is: %s"%link)
            if not self.hasCrawedUrl(link):
                self._getPage(browser, link)
                res = self.getResponse(link, browser)
                if self.satisfy_craw(res):
                    self.crawedAppend(link)
                    self.extract_page_content(res)
                else:
                    self._getPage(browser, link)
                    self.crawedAppend(link)
                    self.craw_sub_page(browser)
