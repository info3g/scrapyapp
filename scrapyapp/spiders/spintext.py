# -*- coding: utf-8 -*-
import scrapy
from scrapy.exceptions import CloseSpider
from copy import copy
from ..models import Review
import json
from pprint import pprint

PROTECTED_TERMS = ['moving', 'movers', 'relocation', 'moving Company', 'moving companies']


class SpintextSpider(scrapy.Spider):
    name = 'spintext'
    custom_settings = {
        'DOWNLOAD_DELAY': 7,
        'CONCURRENT_REQUESTS': 1
    }

    def start_requests(self):
        requests = []
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

        reviews = Review.filter(processed_text=None).order_by(Review.date_saved.desc()).limit(25)
        for review in reviews:
            data['text'] = review.text
            protected_terms = copy(PROTECTED_TERMS)
            protected_terms.append(review.company.title)
            data['protected_terms'] = '\n'.join(protected_terms)
            requests.append(scrapy.FormRequest(url='http://www.spinrewriter.com/action/api',
                                               formdata=data,
                                               callback=self.parse,
                                               meta=dict(review=review)))
        return requests

    def parse(self, response):
        data = json.loads(response.body_as_unicode())
        if data['status'] == 'ERROR':
            raise CloseSpider(reason=data['response'])
        review = response.meta['review']
        review.processed_text = data['response']
        review.save()
