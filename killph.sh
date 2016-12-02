ps -ef | grep "phantomjs"| awk '{print $2}'| xargs kill -9

