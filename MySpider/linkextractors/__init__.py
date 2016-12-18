from six.moves.urllib.parse import urljoin
from scrapy.link import Link
from scrapy.utils.misc import arg_to_iter, rel_has_nofollow
from scrapy.utils.python import unique as unique_list, to_native_str

import Scrapy.linkextractors.LxmlParserLinkExtractor
import Scrapy.linkextractors.LinkExtractor
from scrapy.linkextractors import FilteringLinkExtractor

class MyLxmlParserLinkExtractor(LxmlParserLinkExtractor):
	def __init__(self, tag="a", attr="href", process=None, unique=False):
		super(MyLxmlParserLinkExtractor, self)(tag, attr, process, unique)

	def _extract_links(self, selector, response_url, response_encoding, base_url):
        links = []
        # hacky way to get the underlying lxml parsed document
        for el, attr, attr_val in self._iter_links(selector.root):
            # pseudo lxml.html.HtmlElement.make_links_absolute(base_url)
            try:
                attr_val = urljoin(base_url, attr_val)
            except ValueError:
                continue
            else:
                if base_url == "http://www.bjpc.gov.cn/zwxx/zcfg/xcwj/zcwj/":
                   pdb.set_trace() 
                end
                url = self.process_attr(attr_val)
                if url is None:
                    continue
            url = to_native_str(url, encoding=response_encoding)
            # to fix relative links after process_value
            url = urljoin(response_url, url)
            link = Link(url, _collect_string_content(el) or u'',
                        nofollow=rel_has_nofollow(el.get('rel')))
            links.append(link)
        return self._deduplicate_if_needed(links)


class MyLinkExtractors(FilteringLinkExtractor):
	def __init__(self, allow=(), deny=(), allow_domains=(), deny_domains=(), restrict_xpaths=(),
                 tags=('a', 'area'), attrs=('href',), canonicalize=True,
                 unique=True, process_value=None, deny_extensions=None, restrict_css=()):
        #super(MyLinkExtractors, self).__init__(allow, deny, allow_domains, deny_domains, restrict_xpaths,
        #         tags, attrs, canonicalize, unique, process_value, deny_extensions, restrict_css)
        tags, attrs = set(arg_to_iter(tags)), set(arg_to_iter(attrs))
        tag_func = lambda x: x in tags
        attr_func = lambda x: x in attrs
        lx = MyLxmlParserLinkExtractor(tag=tag_func, attr=attr_func,
            unique=unique, process=process_value)
        super(MyLinkExtractors, self).__init__(lx, allow=allow, deny=deny,
            allow_domains=allow_domains, deny_domains=deny_domains,
            restrict_xpaths=restrict_xpaths, restrict_css=restrict_css,
            canonicalize=canonicalize, deny_extensions=deny_extensions)

    def extract_links(self, response):
        base_url = get_base_url(response)
        if self.restrict_xpaths:
            docs = [subdoc
                    for x in self.restrict_xpaths
                    for subdoc in response.xpath(x)]
        else:
            docs = [response.selector]
        all_links = []
        for doc in docs:
            links = self._extract_links(doc, response.url, response.encoding, base_url)
            all_links.extend(self._process_links(links))
        return unique_list(all_links)
