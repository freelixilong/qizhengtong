#coding:utf-8
#
from selenium import webdriver
from pyvirtualdisplay import Display
import os
import sys
import settings
import pymongo
from scrapy.settings import  Settings
from  spiders import CommSpider
from  spiders import ActionSpider
import pdb

def get_project_settings():
    settings = Settings()
    settings.setmodule("settings", priority='project')
    return settings

def get_firefox_profile():
    profile = webdriver.FirefoxProfile()
    profile.set_preference('network.proxy.type', 1)#默认是0，就是直接连接；1就是手工配置代理
    profile.set_preference('network.proxy.http', '59.110.47.98')
    profile.set_preference('network.proxy.http_port', 8050)
    profile.set_preference('network.proxy.ssl', '59.110.47.98')
    profile.set_preference('network.proxy.ssl_port', 8050)
    profile.update_preferences()
    return profile

if __name__ == '__main__':
    print 'START'
#from pyvirtualdisplay import Display
    #profile = webdriver.FirefoxProfile()
    #profile.set_preference("browser.startup.homepage", "about:blank")
    #profile.set_preference("startup.homepage_welcome_url", "about:blank")
    #profile.set_preference("startup.homepage_welcome_url.additional", "about:blank")

    #profile.assume_untrusted_cert_issuer =True
    #profile.accept_untrusted_certs = True
    #driver = webdriver.Firefox(profile)
    display = Display(visible=0, size=(800, 600))
    display.start()
    #browser = webdriver.Firefox()
    #profile = get_firefox_profile()
    browser = webdriver.Firefox()
    try:
        setting = get_project_settings()
        argc = len(sys.argv)
        print "get argc %d"%argc
        if argc == 3:
            startUrl = sys.argv[2]
            site = sys.argv[1]
            print "start crawl from %s"%startUrl
            spider.start_once(site= site, startUrl = startUrl)
        else:
            client = pymongo.MongoClient(setting.get('MONGO_URI'))
            db = client[setting.get('MONGO_DATABASE', 'test')]
            reses = db.GovDepartment.find({"key": {"$ne":""}})
            for res in reses:
                #spider = CommSpider(browser, setting)
                spider = ActionSpider(browser, setting)
                spider.start(res["key"], startUrl =res["link"])
    except Exception as e:
        print "%s: %s"%("main.py", e.message)

    finally:
        spider.close()
        browser.close()
    print 'END'
