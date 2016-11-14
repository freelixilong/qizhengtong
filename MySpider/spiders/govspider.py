# -*- coding: utf-8 -*-
import re
import logging
import six

import scrapy
from MySpider.items import PageContentItem 
from scrapy.utils.sitemap import Sitemap, sitemap_urls_from_robots
from scrapy.spiders import Spider
from scrapy.http import Request, XmlResponse
from scrapy.utils.sitemap import Sitemap, sitemap_urls_from_robots
from scrapy.utils.gz import gunzip, is_gzipped
from scrapy.linkextractors import LinkExtractor
from scrapy.utils.python import unique as unique_list

logger = logging.getLogger(__name__)

class GovSpider(Spider):
    name = "GovSpider"
    allowed_domains = ["bjpc.gov.cn"]
    start_urls = [
        "http://www.bjpc.gov.cn/",
    ]
    start_host = "http://www.bjpc.gov.cn/"
    filter_urls = []
    clawed_urls = []
    #def __init__(self, deny = '', filter_urls = [], condition = "", title = '', content = "", 
    #    date = "", *a, **kw):
    def __init__(self, url = 'bj', *a, **kw):
        super(GovSpider, self).__init__(*a, **kw)
        #if deny != '':
            #self.deny = True  # the filter_urls is the deny to craw   
        #else:
        #    self.allow = False # the filter_urls is the allow to craw
        #self.filter_urls = filter_urls
        fo = open("test.txt", "w")
        fo.write( url )
        fo.close()
        self.deny = True
        self.page_urls = []
        self.condition = "//div[@class='dbox container']"  #condtion应该为抓取符合条件的页面的xpath <div class="dbox container">
        self.titleX = '//*[@id="container"]/div[6]/h1' #查找的 页面title的xpath
        self.contentX = '//*[@id="container"]/div[6]/div[1]' #查找的 页面content的xpath
        self.dateX = '//*[@id="container"]/div[6]/h2/span[2]' #查找的 页面上关键日期的xpath

    def parse(self, response):
        for sel in response.xpath('//ul/li'):
            item = DmozItem()
            item['title'] = sel.xpath('a/text()').extract()
            item['link'] = sel.xpath('a/@href').extract()
            item['desc'] = sel.xpath('text()').extract()
            yield item

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

    def set_start_urls(urls, host):
        self.start_urls = urls
        self.start_host = host

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, self._parse_response)
            self.clawed_urls.append(url)

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
                    yield Request(link.url, self._parse_response)
                    if self.satisfy_craw(response): #符合条件就抓取该页面
                        yield self.get_item(response, link.url)
                    self.clawed_urls.append(link.url)

        #filename = response.url.split("/")[-2]
        #with open(filename, 'wb') as f:
        #    f.write(response.body)
    def get_item(self, response, url):
        title = response.xpath(self.titleX)
        content = response.xpath(self.contentX)
        date = response.xpath(self.dateX)
        logger.warning('get_item title %s' % title)
        logger.warning('get_item content %s' % content)
        logger.warning('get_item date %s' % date)
        return PageContentItem(title = title, content = content, date = date)
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