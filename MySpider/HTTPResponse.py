# code: UTF-8

from scrapy.http.response.text import TextResponse
class MyResponse(TextResponse):
    def __init__(self, *args, **kwargs):
        super(MyResponse, self).__init__(*args, **kwargs)
        
    def response_is_error(self):
        
