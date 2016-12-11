# code: UTF-8

# Define here the download middleware
#


import base64
class MyCustomDownloaderMiddleware(object):
# overwrite process request
    def process_request(self, request, spider):
        # Set the location of the proxy
        request.meta['proxy'] = "http://localhost:8000/proxy/"

        # Use the following lines if your proxy requires authentication
        proxy_user_pass = "scrapy:scrapy.123"
        # setup basic authentication for the proxy
        encoded_user_pass = base64.b64encode(proxy_user_pass)
        request.headers['Proxy-Authorization'] = 'Basic ' + encoded_user_pass