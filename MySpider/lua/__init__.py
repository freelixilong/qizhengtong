# code: UTF-8

proxyServer = '''
function main(splash)
	splash:init_cookies(splash.args.cookies)
	assert(splash:go{
		splash.args.url,
		headers=splash.args.headers,
		http_method=splash.args.http_method,
		body=splash.args.body,
	})
	assert(splash:wait(0.5))

	local entries = splash:history()
	local last_response = entries[#entries].response
	return {
		url = splash:url(),
		headers = last_response.headers,
		http_status = last_response.status,
		cookies = splash:get_cookies(),
		html = splash:html(),
	}
end








 '''