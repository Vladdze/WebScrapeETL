
import scrapy
from scrapy.item import Item, Field


class LinkedInItem(Item):
    position = Field()
    details = Field()
    listed = Field()
    company_name = Field()
    company_link = Field()
    location = Field()

class IndeedItem(Item):
    position = Field()
    location = Field()
    keyword = Field()
    jobkey = Field()
    company = Field()
    jobTitle = Field()
    details = Field()


