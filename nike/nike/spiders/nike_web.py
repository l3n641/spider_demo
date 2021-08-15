import scrapy
import js2py
from scrapy import Request
from ..items import NikeItem
import urllib.parse


class NikeWebSpider(scrapy.Spider):
    name = 'nike_web'
    allowed_domains = ['www.nike.com', 'api.nike.com']
    start_url = 'https://www.nike.com/'

    def start_requests(self):
        yield scrapy.Request(url=self.start_url, method="GET", callback=self.get_product_category)

    def get_product_category(self, response):
        result = response.selector.re("(window.__MOBILENAV_STATE =.+)")
        if len(result) != 1:
            raise RuntimeError("没找到产品类别")
        data = js2py.eval_js(result[0]).to_dict()
        sub_category_list = []
        for index in range(0, len(data["0"])):
            key = f"0,{index}"
            if (sub_category := data.get(key)):
                sub_category_list = sub_category_list + sub_category

        for category in sub_category_list:
            if category.get("href"):
                yield scrapy.Request(category.get("href"), self.get_product_index_page)

    def get_product_index_page(self, response):
        country = 'cn'
        result = response.selector.re("(window.INITIAL_REDUX_STATE=.+)</script>")
        if result:
            data = js2py.eval_js(result[0]).to_dict()
            products = data.get("Wall").get("products")
            for product in products:
                if product.get("url"):
                    url = self.start_url + product.get("url").format(countryLang=country)
                    # yield Request(url, self.get_product_detail)

            endpoint = data.get("Wall").get("pageData").get("next")
            url = self.get_next_page_url(endpoint, country)

            meta = {"country": country}
            yield Request(url, callback=self.parse_next_page, meta=meta)

    def parse_next_page(self, response):
        data = response.json().get("data").get("products")
        country = response.meta.get("country")
        if not data.get("errors"):
            for product in data.get("products"):
                if product.get("url"):
                    url = self.start_url + product.get("url").format(countryLang=country)
                    yield Request(url, self.get_product_detail)

        if data.get("pages").get('next'):
            endpoint = data.get("pages").get("next")
            url = self.get_next_page_url(endpoint, country)
            meta = {"country": country}
            yield Request(url, callback=self.parse_next_page, meta=meta)

    @staticmethod
    def get_next_page_url(endpoint, country="cn"):
        api = "https://api.nike.com/cic/browse/v1?"
        params = {
            "queryid": "products",
            "country": country,
            "endpoint": endpoint,
            "localizedRangeStr": '%7BlowestPrice%7D%20%E2%80%94%20%7BhighestPrice%7D',
        }
        str_params = urllib.parse.urlencode(params)
        return api + str_params

    def get_product_detail(self, response):
        result = response.selector.re("(window.INITIAL_REDUX_STATE=.+)</script>")
        data = js2py.eval_js(result[0]).to_dict()
        products = data.get("Threads").get("products")
        for sku, product in products.items():
            uuid = product.pop("id")
            yield NikeItem(sku=sku, uuid=uuid, url=response.url, **product)
