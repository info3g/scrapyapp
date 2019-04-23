# -*- coding: utf-8 -*-
import scrapy
from ..models import Image, Company
from PIL import Image as PImage
from ftplib import FTP
from io import BytesIO
import os


class ImagesSpider(scrapy.Spider):
    name = 'images'
    # ftp = FTP(host='127.0.0.1', user='root', passwd='123456')
    # ftp_moving = FTP(host='127.0.0.1', user='root@localhost', passwd='123456')

    def start_requests(self):
        # for image in Image.filter(downloaded=False):
        #     yield scrapy.Request(url=image.url, callback=self.parse, meta=dict(image=image))
        for company in Company.filter(logo_downloaded=False):
            yield scrapy.Request(url=company.logo, callback=self.parse, meta=dict(company=company))

    def parse(self, response):
        if not response.body:
            return

        pimage = PImage.open(BytesIO(response.body))
        f = BytesIO()
        pimage.save(f, 'JPEG', quality=30, optimize=True)
        f.seek(0)

        image = response.meta.get('image')
        company = response.meta.get('company')

        if image:
            fname = f'image_{image.id}.jpg'
            self.ftp.storbinary(f'STOR {fname}', f)
            self.ftp_moving.storbinary(f'STOR {fname}', f)
            image.downloaded = True
            image.filename = fname
            image.save()

        if company:
            fname = os.path.join('logos', f'logo_{company.id}.jpg')
            self.ftp.storbinary(f'STOR {fname}', f)
            self.ftp_moving.storbinary(f'STOR {fname}', f)
            company.logo_downloaded = True
            company.save()

    def closed(self, spider):
        self.ftp.close()
        self.ftp_moving.close()
