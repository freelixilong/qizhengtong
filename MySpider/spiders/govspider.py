# code: UTF-8
import re
import logging
import six

import scrapy,random
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
from scrapy_splash import SplashRequest
from MySpider.lua import proxyServer 
from MySpider.agent import agents
import pymongo
import pdb

proxyProc = proxyServer()
logger = logging.getLogger(__name__)

class GovSpider(Spider):
    name = "GovSpider"
    allowed_domains = ["bjpc.gov.cn"]
    start_urls = []
    start_host = "http://www.bjpc.gov.cn/"
    filter_urls = []
    init_db = False
    depart = ""
    nextPages = []
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
        self.clawed_urls = []
        self.site_urls = []
        self.started = False


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
        #self.start_host = res["link"]
        for nextPage in res["nextPageXpath"]:
            self.nextPages.append(nextPage)
        self.fields = {}
        self.init_db = True
        self.internal_err = False
        self.link_extractor = LinkExtractor(allow=[self.start_host], deny=(), allow_domains=(), deny_domains=(), restrict_xpaths=(),
                 tags=('a', 'area'), attrs=('href',), canonicalize=True, unique=True, process_value=None, deny_extensions=None, restrict_css=())

        for (k, v) in res["fields"].items():
            self.fields[k] = v
    def _Request(self, url):
        #header= {"site": url, "sitebase": self.start_host} for headless phantomjs
        agent = random.choice(agents)
        headers={
            "User-Agent":agent,
            "Referer":url,
        }
        return SplashRequest(url, self._parse_response,
            endpoint='execute',
            cache_args=['lua_source'],
            args={'lua_source': proxyProc},
            headers=headers,
            #dont_obey_robotstxt = True,
        )
 
    def start_requests(self):
        if not self.init_db:
            self.initial_db()

        if self.internal_err:
            raise NotSupported()
        for url in self.start_urls:
            self.crawedAppend(url)
            yield self._Request(url)
    def closed(self, reason):
        logger.warning('self mongo db closed')
        self.client.close()

    def _parse_response(self, response):
        site_urls = []
        if response.url.endswith('/robots.txt'):
            for url in sitemap_urls_from_robots(response.text):
                if not self._is_filter_url(url) and not self.hasCrawedUrl(url):
                   site_urls = self.add_urls_noduplicate(url)            
        else:
            body = response.body
            if body is None:
                logger.warning("Ignoring invalid sitemap: %(response)s",
                               {'response': response}, extra={'spider': self})
                return
            #LinkExtractor
           
            site_urls = self.link_extractor.extract_links(response)
            site_urls = self.add_urls_noduplicate(site_urls)
            if self.satisfy_craw(response):
                yield self.get_item(response)

        for url in site_urls:
            #logger.warning('_parse_response got lnk url %s' % link.url)
            if not self.hasCrawedUrl(url):
                self.crawedAppend(url)
                yield self._Request(url)
    def get_item(self, response):
        il = PageItemLoader(item=PageContentItem(depart = self.depart), response=response)
        for (k, v) in self.fields.items():
            if k == "link":
                il.add_value('link', response.url)
            else:
                xpath = v["select"][0]["xpath"]
                il.add_xpath(k, xpath) #only support simple select current

        return il.load_item()
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