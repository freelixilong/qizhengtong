# -*- coding: utf-8 -*-
import re
import logging
import six

import scrapy
import scrapy.spiders.Spider
import MySpider.items
from scrapy.utils.sitemap import Sitemap, sitemap_urls_from_robots
from scrapy.spiders import Spider
from scrapy.http import Request, XmlResponse
from scrapy.utils.sitemap import Sitemap, sitemap_urls_from_robots
from scrapy.utils.gz import gunzip, is_gzipped

logger = logging.getLogger(__name__)

class GovSpider(Spider):
    name = "GovSpider"
    allowed_domains = ["dmoz.org"]
    start_urls = [
        "http://www.bjpc.gov.cn/",
    ]
    start_host = "http://www.bjpc.gov.cn/"
    filter_urls = []
    clawed_urls = []
    def __init__(self, *a, **kw):
        super(GovSpider, self).__init__(*a, **kw)
        if kw != None:
            if kw["deny"]:
                self.deny = True  # the filter_urls is the deny to craw
            else:
                self.allow = False # the filter_urls is the allow to craw
            self.filter_urls = kw["filter_urls"]
        else:
            self.deny = True

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
                if not self._is_filter_url(url) and not url in self.clawed_urls:
                    yield Request(url, callback=self._parse_response)
                    self.clawed_urls.append(url)
        else:
            body = self._get_sitemap_body(response)
            if body is None:
                logger.warning("Ignoring invalid sitemap: %(response)s",
                               {'response': response}, extra={'spider': self})
                return

            site_urls = []
            for url in response.xpath('//a/@href').extract():
                if not url.startwith("http://"):
                    site_urls.append(self.start_host + url)
                yield Request(url, self._parse_response)
                yield self.get_item(response, url)
                self.clawed_urls.append(url)

        #filename = response.url.split("/")[-2]
        #with open(filename, 'wb') as f:
        #    f.write(response.body)
    def get_item(self, response, url):
    	
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