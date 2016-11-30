var page = require('webpage').create();
var server = require('webserver').create();
var system = require('system');
var host, port;

if (system.args.length !== 2) {
    console.log('Usage: proxy.js <some port>');
    phantom.exit(1);
} else {
    port = system.args[1];
    port1 =
    var listening = server.listen(port, function (request, response) {
        console.log("GOT HTTP REQUEST");
        console.log(JSON.stringify(request, null, 4));
        content = requestRemoteServer(request)
        // we set the headers here
       
    });
    if (!listening) {
        console.log("could not create web server listening on port " + port);
        phantom.exit();
    }
}
function requestRemoteServer(request, response) {
	if (url == "/robots.txt") {
        response.statusCode = 200;
        response.close();
        return;
    }
    page.open(url, function (status) {
        if (status !== 'success') {
            console.log('FAIL to load the address');
            return null;
        } else {
            response.statusCode = 200;
            response.headers = {"Cache": "no-cache", "Content-Type": "text/html"};
          
            response.write(page.content);
            // note: writeBody can be called multiple times
            response.close();
            return 
        }
        
    });
}