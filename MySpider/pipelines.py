# code: UTF-8

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
#import pymongo
import requests
import json
from scrapy.exceptions import DropItem
import pdb
import logging
logger = logging.getLogger(__name__)
class Pipeline(object):

    def __init__(self, server_uri):
        self.server_uri = server_uri

    def encode_field(self, field):
        if (isinstance(field, str)):      
            return field#field.encode("utf-8")
        elif(isinstance(field,list)):
            if(isinstance(field[0],unicode)):
                return field[0].encode("utf-8")
        elif(isinstance(field, unicode)):
            return field.encode("utf-8")
        return field

    def getRestfulAPIData(self, item):
        url = self.server_uri + "/api/1.0"
        jsn = {}
        if item["depart"] == "" or item["section"] == "" or item["title"] == "" or item["link"] == "" or item["date"] == "":
               raise 
        
        jsn["mkey"] = self.encode_field(item["depart"])
        jsn["subKey"] = self.encode_field(item["section"])
        #jsn["action"] = "post"
        if item["title"]:
            data = {}
            data["title"] = self.encode_field(item["title"])
            data["link"] = self.encode_field(item["link"])
            data["date"] = self.encode_field(item["date"])
            #pdb.set_trace()
            for k in item["optionFields"].keys():
                   data[self.encode_field(k)] = self.encode_field(item["optionFields"][k])
            jsn["data"]= data

        return (url, jsn)

    def send_item(self, item):
        try:
            headers = {'content-type':'application/json'}
            (url, jsn) = self.getRestfulAPIData(item)
            #logger.warning('process_item title %s' % item["title"])
            pdb.set_trace()
            logger.warning('process_item post: %s' % json.dumps(jsn, ensure_ascii=False))
            #with open("item.json", 'a+') as t:
            #    t.write(json.dumps(jsn, ensure_ascii=False) + "\n")
            #    t.close()
            r = requests.post(url, data = json.dumps(jsn, ensure_ascii=False), headers = headers)  #will stuck here a little, need improving
        except Exception, e:
            raise DropItem("process_item the server(%s) response error" % self.server_uri)
            

