# code: UTF-8

def proxyServer(nextPage):
	proxy = '''
	function main(splash)
		splash:init_cookies(splash.args.cookies)
		assert(splash:go{
			splash.args.url,
			headers=splash.args.headers,
			http_method=splash.args.http_method,
			body=splash.args.body,
		})
		assert(splash:wait(0.5))
		local nextP = nil
		for _, nextP in ipairs(splash.args.nextPage) do
			local el = splash:select(nextP)
		    if el then
		         local bounds = el:bounds()
                 el:mouse_click{x=bounds.width/2, y=bounds.height/2})
                 splash:wait(0.1)
                 break
		    end
		end
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
	return proxy
