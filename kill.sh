ps -ef | grep "/home/xlong/GovScrapy/virenv/bin/python2 /home/xlong/GovScrapy/virenv/bin/scrapy"| awk '{print $2}'| xargs kill -9

