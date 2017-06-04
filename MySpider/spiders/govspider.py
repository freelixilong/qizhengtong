# code: UTF-8
import re
import logging
import six

import scrapy,random
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
    def __init__(self, browser ,settings,*a, **kw):
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
        logger.info('spider is finished!')

    def _init_from_db(self):
        self.client = pymongo.MongoClient(self.settings.get('MONGO_URI'))
        self.db = self.client[self.settings.get('MONGO_DATABASE', 'test')] 
    def destroy_init_data(self):
        self.condition = ""
        del self.start_urls 
        del self.nextPages
        del self.fields
        self.init_db = False
        del self.link_extractor
        #self.start_host = res["link"]
      
    def start(self):
        res = self.db.GovDepartment.find({"key":{"$ne":""}})

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

    def set_start_urls(self, urls, host):
        self.start_urls.add(urls)
        self.start_host = host

    def _init_gov_data(self, gov):
       
        self.condition = gov["condition"]
        self.start_urls.append(gov["link"])
        #self.browser = webdriver.Firefox()
        #self.start_host = res["link"]
        if type(gov["nextPageXpath"])==str:
            self.nextPages = gov["nextPageXpath"] 
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

    def start_requests(self):
        for url in self.start_urls:
            self.request(url)

    def close(self):
        logger.warning('self mongo db closed')
        self.client.close()

    def request(self, url):
        try:
            logger.info("start crawl url: %s"%url)
            browser = self.browser.get(url)
            logger.info("crawled url: %s"%url)
            pdb.set_trace()
            page = copy.deepcopy(browser.page_source)
           
            self.crawedAppend(url)
            res = TextResponse(url,body=page)
            site_urls = self.link_extractor.extract_links(res)
            site_urls = self.add_urls_noduplicate(site_urls)
            
            if self.satisfy_craw(res):
                item =  self.get_item(res)
                self.save_item(item)

            for url in site_urls:
                if not self.hasCrawedUrl(url):
                    self.request(url) ##once come here, the browser is dirty data

            if self.has_nextpage(page):
                self.craw_next_pages(url)

        except Exception, e:
            logger.warning('exceptions happended %s'%e.message)
        else:
            return
 
    def craw_next_pages(self, url):
        browser = self.browser.get(url)
        page = browser.page_source

        class wait_for_next_element(object):
            def __init__(self, xpath):
                #self.locator = locator
                self.xpath = xpath
            def __call__(self, driver):
                #elements = [element for element in EC._find_elements(driver, self.locator) if EC.element_to_be_clickable(element)]
                elements = driver.find_element_by_xpath(this.nextPage)
                for elment in elements:
                    if EC.element_to_be_clickable(element):
                        return True
                return False        
             
        try:
            tempBrowser = webdriver.Firefox()
            while self.browser.find_element_by_xpath(this.nextPage):
                self.browser.find_element_by_xpath(this.nextPage).click()   
                WebDriverWait(self.browser, 10).until(wait_for_next_element(this.nextPage)) #(BY.NAME, "body")
                page = self.browser.page_source
                res = TextResponse(url,body=page)

                site_urls = self.link_extractor.extract_links(res)
                site_urls = self.add_urls_noduplicate(site_urls)
                for url in site_urls:
                    res = TextResponse(url,body=tempBrowser.page_source)
                    if self.satisfy_craw(res):
                        tempBrowser.get(url)
                        item =  self.get_item(res)
                        self.save_item(item)     
            
        except Exception, e:
            logger.warning('craw_next_pages failed %s'%e.msg)
        finally:
            pdb.set_trace()
            tempBrowser.close()
        
    def get_item(self, response):
        il = PageItemLoader(item=PageContentItem(depart = self.depart), response=response)
        il.add_value('link', response.url)
        for (k, v) in self.fields.items():
                il.add_xpath(k, v) #only support simple select current

        return il.load_item()
    def save_item(self, item):
        self.pipeline.send_item(item)

    def satisfy_craw(self, response):
        data = response.xpath(self.condition).extract()
        if data != []:
            return True
        return False
    def crawedAppend(self, url):
        if not self.hasCrawedUrl(url):
            self.clawed_urls.append(url)

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
