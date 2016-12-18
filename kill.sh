ps -ef | grep "GovSpider"| awk '{print $2}'| xargs kill -9

