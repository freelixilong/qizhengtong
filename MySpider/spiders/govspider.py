# code: UTF-8
import re
import logging
import six

import scrapy
from MySpider.items import PageContentItem 
from MySpider.items import PageItemLoader 
from scrapy.utils.sitemap import Sitemap, sitemap_urls_from_robots
from scrapy.spiders import Spider
from scrapy.http import Request, XmlResponse
from scrapy.utils.sitemap import Sitemap, sitemap_urls_from_robots
from scrapy.utils.gz import gunzip, is_gzipped
from scrapy.linkextractors import LinkExtractor
from scrapy.utils.python import unique as unique_list
from scrapy.exceptions import NotSupported
import pymongo
import pdb

logger = logging.getLogger(__name__)

class GovSpider(Spider):
    name = "GovSpider"
    allowed_domains = ["bjpc.gov.cn"]
    start_urls = []
    start_host = "http://www.bjpc.gov.cn/"
    filter_urls = []
    clawed_urls = []
    init_db = False
    depart = ""
    #def __init__(self, deny = '', filter_urls = [], condition = "", title = '', content = "", 
    #    date = "", *a, **kw):
    def __init__(self, depart = "site", *a, **kw):
        super(GovSpider, self).__init__(*a, **kw)
        #if deny != '':
            #self.deny = True  # the filter_urls is the deny to craw   
        #else:
        #    self.allow = False # the filter_urls is the allow to craw
        #self.filter_urls = filter_urls
        self.depart = depart
        self.internal_err = True
        self.deny = True
        self.page_urls = []

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
        pdb.set_trace()
    def initial_db(self):
        try:
            self.client = pymongo.MongoClient(self.settings.get('MONGO_URI'))
            self.db = self.client[self.settings.get('MONGO_DATABASE', 'test')] 
            res = self.db.GovDepartment.find_one({"key":self.depart})
            if res is None:
                self.internal_err = True
                raise NotSupported()
                return
        except Exception, e:
            logger.error("mongodb got errror: %s",self.settings.get('MONGO_URI'))
            self.internal_err = True
        #pdb.set_trace()
        self.condition = res["condition"]
        self.start_urls.append(res["link"])
        #self.fields = res["fields"]
        self.fields = {}
        self.init_db = True
        self.internal_err = False
        for (k, v) in res["fields"].items():
            self.fields[k] = v
    def start_requests(self):
        if not self.init_db:
            self.initial_db()

        if self.internal_err:
            raise NotSupported()
        for url in self.start_urls:
            yield Request(url, self._parse_response)
            self.clawed_urls.append(url)
    def closed(self):
        logger.warning('self mongo db closed')
        self.client.close()

    def _parse_response(self, response):
        if response.url.endswith('/robots.txt'):
            for url in sitemap_urls_from_robots(response.text):
                if not self._is_filter_url(url) and not (url in self.clawed_urls):
                    yield Request(url, callback=self._parse_response)
                    self.clawed_urls.append(url)
        else:
            body = response.body
            if body is None:
                logger.warning("Ignoring invalid sitemap: %(response)s",
                               {'response': response}, extra={'spider': self})
                return

            link_extractor = LinkExtractor(allow=[self.start_host], deny=(), allow_domains=(), deny_domains=(), restrict_xpaths=(),
                 tags=('a', 'area'), attrs=('href',), canonicalize=True, unique=True, process_value=None, deny_extensions=None, restrict_css=())

            site_urls = link_extractor.extract_links(response)
            logger.warning('_parse_response for %s' % response.url)
            for link in site_urls:
                logger.warning('_parse_response got lnk url %s' % link.url)
                if not link.url in self.clawed_urls:
                    self.clawed_urls.append(link.url)
                    yield Request(link.url, self._parse_response)
                    if self.satisfy_craw(response):
                        yield self.get_item(response, link.url)
    def get_item(self, response, url):
        #pdb.set_trace()
        il = PageItemLoader(item=PageContentItem(), response=response)
        for (k, v) in self.fields.items():
            if k == "link":
                il.add_value('link', url)
            else:
                xpath = v["select"][0]["xpath"]
                il.add_xpath(k, xpath) #only support simple select current

        return il.load_item()
    def satisfy_craw(self, response):
        if response.xpath(self.condition) != "":
            return True
        return False
           
    def _get_sitemap_body(self, response):
        """Return the sitemap body contained in the given response,
        or None if the response is not a sitemap.
        """
        if isinstance(response, XmlResponse):
            return response.body
        elif is_gzipped(response):
            return gunzip(response.body)
        elif response.url.endswith('.xml'):
            return response.body
        elif response.url.endswith('.xml.gz'):
            return gunzip(response.body)