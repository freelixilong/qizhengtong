# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader import ItemLoader
from scrapy.contrib.loader.processor import TakeFirst, MapCompose, Join

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
        super(PageItemLoader, self).__init__(item, selector, response, parent, **context)

    def load_item(self):
        item = self.item
        for field_name in tuple(self._values):
            value = self.get_output_value(field_name)
            if value is not None:
                if hasattr(item, field_name):
                    item[field_name] = value
                else:
                    item["fields"][field_name] = value
        return item
