# code: UTF-8
import re
import logging
import six

#import scrapy,random
from items import PageContentItem
from items import PageItemLoader
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
from pipelines import Pipeline
import copy
import pymongo
import pdb
from logger import getLogger

#proxyProc = proxyServer()
logger = getLogger()

class GovSpider():
    name = "GovSpider"
    start_urls = []
    start_host = "http://www.bjpc.gov.cn/"
    filter_urls = []
    init_db = False
    depart = ""
    nextPages = []
    #def __init__(self, deny = '', filter_urls = [], condition = "", title = '', content = "",
    #    date = "", *a, **kw):
    def __init__(self, browser ,settings, *a, **kw):
        self.browser = browser
        self.settings = settings
        if self.browser:
            self._init_from_db()
        self.internal_err = True
        self.deny = True
        self.clawed_urls = []
        self.site_urls = []
        self.started = False
        self.pipeline = Pipeline(self.settings.get('MYSERVER_URI'))
        self.proxyUrl = self.settings.get("SPLASH_URL")
        logger.info('spider init is finished!')


    def _init_from_db(self):
        self.client = pymongo.MongoClient(self.settings.get('MONGO_URI'))
        self.db = self.client[self.settings.get('MONGO_DATABASE', 'test')]

    def start_once(self, site= None, startUrl = None):
        res = self.db.GovDepartment.find_one({"key": site})
        self._init_gov_data(res)
        logger.info('start oncec crawl %s!'%startUrl)
        #self.start_requests()
        self.request(startUrl)
        self.destroy_init_data()

    def start(self):
        res = self.db.GovDepartment.find({"key":{"$ne":""}})

        #with open("urls.html", 'a+') as t:
            #    t.write(self.browser.page_source.encode("utf-8"))
            #    t.close()
        for gov in res:
            self._init_gov_data(gov)
            logger.info('start crawl %s!', gov['link'])
            self.start_requests()
            self.destroy_init_data()

    def _is_filter_url(self, url):
        if not url.startwith(self.start_host):
            return True #only claw in self site
        if self.deny:
            for u in self.filter_urls:
                if url.startwith(u):
                    return True
            return False
        else:
            for u in self.filter_urls:
                if url.startwith(u):
                    return False
            return True
    def destroy_init_data(self):
        self.condition = ""
        self.start_urls =[]
        self.nextPages = []
        del self.fields
        self.init_db = False
        del self.link_extractor
        self.f.close()
        #self.start_host = res["link"]

    def _init_gov_data(self, gov):

        try:
            self.condition = gov["condition"]
            self.start_urls.append(gov["link"])
            #self.browser = webdriver.Firefox()
            self.start_host = gov["link"]
            self.f = open(gov["key"] + ".txt", 'a+')

            if type(gov["nextPageXpath"])==str or type(gov["nextPageXpath"])==unicode:
                self.nextPages.append(gov["nextPageXpath"])
            else:
                for nextPage in gov["nextPageXpath"]:
                    self.nextPages.append(nextPage)
            self.fields = {}
            self.init_db = True
            self.internal_err = False
            self.link_extractor = LinkExtractor(allow=[self.start_host], deny=(), allow_domains=(), deny_domains=(), restrict_xpaths=(),
                     tags=('a', 'area'), attrs=('href',), canonicalize=True, unique=True, process_value=None, deny_extensions=None, restrict_css=())

            for field in gov["fields"]:
                self.fields[field["name"]] = field["xpath"]
        except Exception as e:
            print "_init_gov_data error: %s"%e.message

    def start_requests(self):
        for url in self.start_urls:
            self.request(url)

    def close(self):
        logger.warning('self mongo db closed')
        self.client.close()
        self.f.close()
    def _getPage(self, url, browser):
        newUrl = "%s%s%s%s"%(self.proxyUrl, "?url=", url, "&timeout=10&wait=0.5")
        print "get newUrl %s"%newUrl
        self.currentUrl = url
        browser.get(newUrl)

    def request(self, url):
        try:
            #logger.info("start crawl url: %s"%url)
            self._getPage(url, self.browser)
            logger.info("crawled url: %s"%url)
            self.crawedAppend(url)
            res = TextResponse(url,body=self.browser.page_source.encode("utf-8"))
            site_urls = self.link_extractor.extract_links(res)
            site_urls = self.add_urls_noduplicate(site_urls)
            #with open("temp.html", 'w') as t:
            #    t.write(self.browser.page_source.encode("utf-8"))
            #    t.close()
            if self.satisfy_craw(res):
                item =  self.get_item(res)
                self.save_item(item)
            nextXpath = self.get_next_page_xpath(self.browser)

            #if nextXpath:
            #    self.craw_next_pages(nextXpath, site_urls)

            for url in site_urls:
                if not self.hasCrawedUrl(url):
                    self.request(url) ##once come here, the browser is dirty data

        except Exception as e:
            logger.warning('exceptions happended %s'%e.message)
        else:
            return

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
                res = TextResponse(self.currentUrl,body=self.browser.page_source.encode("utf-8"))
                self.crawedAppend(self.currentUrl)
                site_urls = self.link_extractor.extract_links(res)
                site_urls = self.add_urls_noduplicate(site_urls)
                for url in site_urls:
                    self._getPage(url, tempBrowser)
                    logger.info("crawled n url: %s"%url)
                    #self.crawedAppend(url)
                    res = TextResponse(url,body=tempBrowser.page_source.encode("utf-8"))
                    if self.satisfy_craw(res):
                        self.crawedAppend(url)
                        item =  self.get_item(res)
                        self.save_item(item)
                    else:
                        self._add_url_nodup(url, dstArr)
                self.browser.find_element_by_xpath(nextXpath).click()
                nextElement = wait_for_next_element(nextXpath)
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

    def get_item(self, response):
        il = PageItemLoader(item=PageContentItem(depart = self.depart), response=response)
        il.add_value('link', response.url)
        for (k, v) in self.fields.items():
                il.add_xpath(k, v) #only support simple select current

        return il.load_item()
    def save_item(self, item):
        self.pipeline.send_item(item)

    def satisfy_craw(self, response):

        for condition in self.condition:
            data = response.xpath(condition).extract()
            if data != []:
                return True

        return False
    def crawedAppend(self, url):
        if not self.hasCrawedUrl(url):
            self.clawed_urls.append(url)
            self.f.write(url.encode("utf-8")+"\n")

    def hasCrawedUrl(self, url):

        if not url in self.clawed_urls:
            return False
        return True
    def add_urls_noduplicate(self, site_urls):
        res = []
        if isinstance(site_urls, list):
            for link in site_urls:
                self._add_url_nodup(link.url, res)
        else:
            self._add_url_nodup(site_urls, res)
        return res

    def _add_url_nodup(self, url, dstArr):
        if not url in dstArr:
            dstArr.append(url)
