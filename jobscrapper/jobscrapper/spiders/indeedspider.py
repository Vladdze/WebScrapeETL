import re
import json
from itertools import product
import scrapy
from urllib.parse import urlencode
from scrapy.http import Request
from jobscrapper.items import IndeedItem

class IndeedJobSpider(scrapy.Spider):
    name = "indeedspider"

    def get_indeed_search_url(self, keyword, location, offset=0):
        parameters = {
            "q": keyword,
            "l": location,
            "filter": 0,
            "start": offset,
        }
        return f"https://www.indeed.com/jobs?{urlencode(parameters)}"

    def start_requests(self):
        keyword_list = ['machine learning engineer', 'data analyst', 'data scientists', 'data engineer']
        location_list = ['Canada', 'USA']

        for keyword, location in product(keyword_list, location_list):
            url = self.get_indeed_search_url(keyword, location)
            yield scrapy.Request(url=url, callback=self.parse_search_results, meta={'keyword': keyword, 'location': location, 'offset': 0})

    def parse_search_results(self, response):
        location = response.meta['location']
        keyword = response.meta['keyword']
        offset = response.meta['offset']

        script_tag = re.findall(r'window.mosaic.providerData\["mosaic-provider-jobcards"\]=(\{.+?\});', response.text)
        if script_tag:
            try:
                json_blob = json.loads(script_tag[0])

                ## LOGIC
                if offset == 0:
                    meta_data = json_blob.get("metaData", {}).get("mosaicProviderJobCardsModel", {}).get("tierSummaries", [])
                    num_results = min(sum(category.get("jobCount", 0) for category in meta_data), self.MAX_RESULTS)

                    for next_offset in range(10, num_results, 10):
                        url = self.get_indeed_search_url(keyword, location, next_offset)
                        yield scrapy.Request(url=url, callback=self.parse_search_results, meta={'keyword': keyword, 'location': location, 'offset': next_offset})

                # EXTRACT JOBS
                for index, job in enumerate(json_blob.get('metaData', {}).get('mosaicProviderJobCardsModel', {}).get('results', [])):
                    jobkey = job.get('jobkey')
                    if jobkey:
                        job_url = f'https://www.indeed.com/m/basecamp/viewjob?viewtype=embedded&jk={jobkey}'
                        yield scrapy.Request(
                            url=job_url,
                            callback=self.parse_job,
                            meta={
                                'keyword': keyword,
                                'location': location,
                                'page': offset // 10 + 1,
                                'position': index,
                                'jobKey': jobkey,
                            }
                        )
            except json.JSONDecodeError:
                self.logger.error('JSON decode error in parse_search_results')

    def parse_job(self, response):
        job_item = IndeedItem()
        
        job_item['location'] = response.meta['location']
        job_item['keyword'] = response.meta['keyword']
        job_item['page'] = response.meta['page']
        job_item['position'] = response.meta['position']
        job_item['jobkey'] = response.meta['jobKey']

        script_tag = re.findall(r"_initialData=(\{.+?\});", response.text)
        if script_tag:
            try:
                json_blob = json.loads(script_tag[0])
                job = json_blob.get("jobInfoWrapperModel", {}).get("jobInfoModel", {})
                
                job_item['company'] = job.get('companyName', '')
                job_item['jobTitle'] = job.get('jobTitle', '')
                job_description = job.get('sanitizedJobDescription', {}).get('content', '')
                job_item['details'] = job_description.strip() if job_description else ''
                
                yield job_item
            except json.JSONDecodeError:
                self.logger.error(f"JSON decode error in parse_job for URL: {response.url}")

    