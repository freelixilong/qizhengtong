#coding:utf-8
#
from selenium import webdriver
from  spiders import GovSpider
from pyvirtualdisplay import Display
import os
import settings 
from scrapy.settings import  Settings
import pdb


def get_project_settings():

    settings = Settings()
    settings.setmodule("settings", priority='project')
    return settings

if __name__ == '__main__': 
    print 'START'
#定义一个火狐浏览器对象
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
    browser = webdriver.Firefox()
    try:
        setting = get_project_settings()

        spider = GovSpider(browser, setting)
        spider.start()
    except Exception, e:
        print "%s: %d: %s"%("main.py", __LINE__, e.message)
   
    finally:
        spider.close()
        browser.close()
    print 'END'
