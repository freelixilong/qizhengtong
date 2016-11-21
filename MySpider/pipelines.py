# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
#import pymongo
import requests
import json

class MyspiderPipeline(object):

    def __init__(self, server_uri):
        self.server_uri = server_uri

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            server_uri=crawler.settings.get('MYSERVER_URI'),
        )

    def open_spider(self, spider):
        #self.client = pymongo.MongoClient(self.mongo_uri)
        #self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        #self.client.close()
    def getRestfulAPIData(item):
    	url = self.server_uri + "/api/1.0"
    	jsn = {}
    	jsn.mkey = item.depart
    	jsn.subKey = item.section
    	jsn.action = "post"
    	if item.title:
    		data = {}
    	    data.title = item.title
    	    data.link = item.link
    	    data.append = item.append
    	    data.date = item.date
    	    data.desc = item.desc
            jsn.data = data

    	return (url, jsn)

    def process_item(self, item, spider):
		try:
			headers = {'content-type': 'application/json',}
			(url, jsn) = self.getRestfulAPIData(item)
			r = requests.post(url, data = json.dump(jsn), headers = headers)  #will stuck here a little, need improving
		except Exception, e:
			raise DropItem("process_item the server(%s) response error" % self.server_uri)
		else:
			if r.status == '404':
                raise DropItem("process_item the server(%s) response error" % self.server_uri)
	        else:
                return item
		finally:
			pass
	        
            

