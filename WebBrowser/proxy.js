var page = require('webpage').create();
var server = require('webserver').create();
var system = require('system');
var host, port;

if (system.args.length !== 2) {
    console.log('Usage: proxy.js <some port>');
    phantom.exit(1);
} else {
    port = system.args[1];
    var listening = server.listen(port, function (request, response) {
        console.log("GOT HTTP REQUEST");
        console.log(JSON.stringify(request, null, 4));
        content = requestRemoteServer(request)
        // we set the headers here
        response.statusCode = 200;
        response.headers = {"Cache": "no-cache", "Content-Type": "text/html"};
        // this is also possible:
        //response.setHeader("foo", "bar");
        // now we write the body
        // note: the headers above will now be sent implictly
        response.write(content);
        // note: writeBody can be called multiple times
        response.close();
    });
    if (!listening) {
        console.log("could not create web server listening on port " + port);
        phantom.exit();
    }
}
function requestRemoteServer(request) {
	var url = request.url;
    console.log("SENDING REQUEST TO:");
    console.log(url);
    page.open(url, function (status) {
        if (status !== 'success') {
            console.log('FAIL to load the address');
            return null;
        } else {
            return page.content
        }
        
    });
}