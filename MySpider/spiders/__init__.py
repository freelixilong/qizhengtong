# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
import pymongo
from items import PageContentItem
from items import PageItemLoader
from scrapy.http.response.text import TextResponse
from pipelines import Pipeline
from logger import getLogger

#proxyProc = proxyServer()
logger = getLogger()
class BaseSpider(object):
    """The most top class."""
    start_urls = []
    start_host = "http://www.bjpc.gov.cn/"
    filter_urls = []
    init_db = False
    depart = ""

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

    def start(self, site, startUrl = None):
        res = self.db.GovDepartment.find_one({"key": site})
        self._init_gov_data(res)
        logger.info('start crawl %s!'%startUrl)
        #self.start_requests()
        self.request(startUrl)
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

            self.fields = {}
            self.init_db = True
            self.internal_err = False
            self.link_extract()
            for field in gov["fields"]:
                self.fields[field["name"]] = field["xpath"]
        except Exception as e:
            print "_init_gov_data error: %s"%e.message
    def link_extract(self):
        self.link_extractor = None

    def start_requests(self):
        for url in self.start_urls:
            self.request(url)

    def close(self):
        logger.warning('self mongo db closed')
        self.client.close()

    def getResponse(self, url, browser):
        res = TextResponse(url,body=browser.page_source.encode("utf-8"))
        return res
    def request(self, url):
        pass

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

from .govspider import CommSpider
