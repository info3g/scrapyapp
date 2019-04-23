# -*- coding: utf-8 -*-
import scrapy
import spintax
import json
import requests
import time
from ..models import Company, Review, Image, db, CompanyM, ReviewM, db_moving


class ReviewsSpider(scrapy.Spider):
    name = 'reviews'
    mode = 'start_only'

    def __init__(self, **kwargs):
        # if mode == 'all' => crawl all reviews
        self.mode = kwargs.get('mode', 'start_only')
        #self.mode = "all"

    def start_requests(self):
        if self.mode == 'all':
            return [scrapy.Request(url='https://www.mymovingreviews.com/moving-companies.php', callback=self.parse_state_list)]
        else:
            return [scrapy.Request(url='https://www.mymovingreviews.com', callback=self.parse_start_page)]

    def parse_state_list(self, response):
        state_lists = response.xpath('//ul[@class="statelist"]')
        for lst in state_lists[:-1]:
            urls = lst.xpath('.//a/@href').extract()
            for url in urls:
                yield scrapy.Request(url=url, callback=self.parse_state)

    def parse_state(self, response):
        company_listings = response.xpath('//a[@class="listing vcard"]/@href').extract()
        for url in company_listings:
            yield scrapy.Request(url=url, callback=self.parse_company)

        pagination = response.xpath('//div[@class="centerPagi"]//ul//a/@href').extract()
        for url in pagination:
            yield scrapy.Request(url=url, callback=self.parse_state)

    def parse_company(self, response):
        # Extracting company data
        company = response.meta.get('company')
        if not company:
            company_json = {}
            company_json['rating'] = int(response.xpath('//div[@class="company_header_title"]//span[contains(@class, "company-rating")]/@class').extract_first().split('rating_')[1])
            company_json['url'] = response.url
            company_json['title'] = response.xpath('//div[@class="company_header_title"]/h1/text()').extract_first()
            company_json['logo'] = response.xpath('//div[@class="company_header_logo"]/img/@src').extract_first()
            company_json['email'] = response.xpath('//img[@src="images/icons/email.png"]/following-sibling::a/text()').extract_first()
            company_json['website'] = response.xpath('//img[@src="images/icons/web.png"]/following-sibling::a/text()').extract_first()
            company_json['phone'] = response.xpath('//span[@class="tel"]/text()').extract_first()
            company_json['address'] = response.xpath('//div[@class="company_info_address"]/text()').extract_first()
            company_json['states'] = response.xpath('//p[contains(text(), "States of operation: ")]/a/text()').extract()
            company = Company.from_json(company_json)
            print("Company")
            print(company)
            company_m = CompanyM.save_data(company_json)
            print("CompanyM")
            print(company_m)
        # Extracting reviews
        reviews = response.xpath('//div[@class="company-reviews-n"]')

        for review_selector in reviews:
            review_json = {}
            review_json['author'] = review_selector.xpath('.//div[@class="reviews-author"]/b/text()').extract_first()
            review_json['date'] = review_selector.xpath('.//div[@class="reviews-date"]/text()').extract_first()
            review_json['rating'] = int(review_selector.xpath('.//span[contains(@class, "company-rating")]/@class').extract_first().split('rating_')[1])
            review_json['company'] = company.id
            review_json['text'] = '\n'.join(review_selector.xpath('.//div[@class="reviewContent"]/p/text()').extract()).strip()

            #Checking if we already have the review in the webpage
            review_check = Review.checkReview(review_json)

            # In case we have the review in the first page we need to add it to the second one
            print("Review Check")
            print(review_check)

            if(review_check):
                print("Review Exists \r\n")
                review_json['text'] = spintax.spin(review_check.processed_text)
                review_json["co_id"] = company_m
                review = review_check
                ReviewM.save_data(review_json,company_m.comp_name,company_m.comp_stripname)
            else:
                print("New Review \r\n")
                spinned_text = self.spin_review_text(review_json['text'])
                review_json["processed_text"] = spinned_text
                review_json['text'] = spintax.spin(spinned_text)
                review = Review.from_json(review_json)
                print("Review Data")
                print(review)
                review_json['text'] = spintax.spin(spinned_text)
                review_json["co_id"] = company_m
                ReviewM.save_data(review_json,company_m.comp_name,company_m.comp_stripname)


        # Going deeped if in scrape_all mode
        if self.mode == 'all':
            pagination = response.xpath('//div[@class="centerPagi"]//ul//a/@href').extract()
            for url in pagination:
                yield scrapy.Request(url=url, callback=self.parse_company, meta=dict(company=company))

    def parse_start_page(self, response):
        companies = response.xpath('//div[@id="movers-company"]//div[@class="home-company"]/strong/a/@href').extract()
        for url in companies:
            yield scrapy.Request(url=response.urljoin(url), callback=self.parse_company)

    def spin_review_text(self,text):
        data = {}
        data['email_address'] = "bishara7@gmail.com"
        data['api_key'] = "5aabd79#aabbcbf_16d726f?aa3a7b5"
        data['action'] = "text_with_spintax"
        data['auto_protected_terms'] = "false"
        data['confidence_level'] = "medium"
        data['nested_spintax'] = "true"
        data['auto_sentences'] = "false"
        data['auto_paragraphs'] = "false"
        data['auto_new_paragraphs'] = "false"
        data['auto_sentence_trees'] = "false"
        data['spintax_format'] = "{|}"
        data['text'] = text 
        data['protected_terms'] = ['moving', 'movers', 'relocation', 'moving Company', 'moving companies']

        response = requests.post("https://www.spinrewriter.com/action/api", data=data)
        data = response.json()
        time.sleep(10)
        return data['response']
    # def closed(self, reason):
    #     # proccess = CrawlerProcess()
    #     # proccess.crawl(ImagesSpider)
