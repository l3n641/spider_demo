# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

from mongoengine import connect
from .mongo_models import NikeProduct


class NikePipeline:

    def open_spider(self, spider):
        mongo_url = spider.settings.get('MONGODB_URL')
        connect('my_db', username='root', password='123456', authentication_source='admin',
                host="mongodb://localhost:27017/spider_data")

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        print(item)
        data = dict(item)
        product = NikeProduct(**data)
        product.save()
        return item
