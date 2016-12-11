# code: UTF-8

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader import ItemLoader
from scrapy.contrib.loader.processor import TakeFirst, MapCompose, Join
import logging
#import chardet
import pdb

logger = logging.getLogger(__name__)

class PageContentItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    depart = scrapy.Field() #bu men, gov 
    section = scrapy.Field() # bankuai
    title = scrapy.Field() #
    link = scrapy.Field()
    date = scrapy.Field()
    optionFields =  scrapy.Field()
    #append = scrapy.Field() #fujian mulu 
   
class PageItemLoader(ItemLoader):
    def __init__(self, item=None, selector=None, response=None, parent=None, **context):
        #response.text = response.text.decode("utf-8")
        super(PageItemLoader, self).__init__(item, selector, response, parent, **context)
        self.response = response

    def load_item(self):
        item = self.item
        item["optionFields"] = {}
        
        for field_name in tuple(self._values):
            value = self.get_output_value(field_name)
            if field_name == "link":
                with open("test.html", 'a+') as t:
                    t.write(self.response.url.encode("utf-8") + "\n")
                    t.close()
            if value is not None:
                try:
                    if item.fields[field_name] != None:
                        item[field_name] = value
                    else:
                        #pdb.set_trace()
                        item["optionFields"][field_name] = value
                except Exception, e:
                    item["optionFields"][field_name] = value

                
        #pdb.set_trace()
        
        return item
    def _get_item_field_attr(self, field_name, key, default=None):
        try:
            value = super(PageItemLoader, self)._get_item_field_attr(field_name, key, default)
        except Exception, e:
            logger.warning('_get_item_field_attr didnot find the attr %s' % field_name)
            value = default
        finally:
            return value
       
