var WebServer = require('webserver');
var system = require('system');
var host, port;

if (system.args.length !== 2) {
    console.log('Usage: proxy.js <some port>');
    phantom.exit(1);
} else {
    port = system.args[1];
    var server = WebServer.create();
    console.log('listen on port:', port);
    var listening = server.listen(port, function (request, response) {
        console.log(JSON.stringify(request, null, 4));
        content = requestRemoteServer(request, response)
        // we set the headers here
       
    });
    if (!listening) {
        console.log("could not create web server listening on port " + port);
        phantom.exit();
    }
}
function requestRemoteServer(request, response) {
    
	var url = request.headers["site"] + request.headers["path"];
    url = "http://" + url;
    console.log("open:", url);
    var page = require('webpage').create();
    page.open(url, function (status) {
        if (status !== 'success') {
            console.log('FAIL to load the address',status);
            response.statusCode = 500;
            response.write('FAIL to load the address:', url);
            response.close();
            
        } else {
            console.log("success open site:", url);
            response.statusCode = 200;
            
            //console.log(page.content.headers);
            //response.headers = page.headers;
            response.write(page.content);
            // note: writeBody can be called multiple times
            response.close(); 
        }
        page.close();
        //callback.apply();
        
    });
}
/*
{
    "headers": {
        
        "Accept-Encoding": "gzip,deflate",
        "Accept-Language": "zh-CN,zh;q=0.8",
        "Connection": "close",
        "Content-Length": "2",
        "Cookie": "proxyIP=127.0.0.1;proxyPort=8088;",
        "Host": "127.0.0.1:8088",
        "Proxy-Authorization": "Basic c2NyYXB5OnNjcmFweS4xMjM=",
        "Referer": "http://10.100.10.223/",
        "User-Agent": "Scrapy/1.2.1 (+http://scrapy.org)",
        "path": "/robots.txt",
        "site": "www.bjpc.gov.cn"
    },
    "httpVersion": "1.0",
    "method": "GET",
    "url": "/index.html"
}*/
