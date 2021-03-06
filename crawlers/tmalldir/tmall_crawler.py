#!/usr/bin/env python2
# -*- coding:utf-8 -*-
import re
import json
from .comment_crawler import CommentCrawler, CrawlException
import lxml.html
from ..shared.httpclient import HTTPClient
from ..shared import create_json


class TmallCrawler(CommentCrawler):

    item_url = "http://detail.tmall.com/item.htm"
    rate_url = "http://rate.tmall.com/list_detail_rate.htm"
    shop_name_url = 'http://{}.tmall.com/search.htm?spm=&pageNo=1'

    def __init__(self):
        self.http = HTTPClient()

    def get_seller_id(self, item_id):
        """\
        Get sellerId from itemId

        Args:
            item_id:

        Raises:
            request.ConnectionError: when failed to connect to the site
            CrawlException: when failed to find seller id from response page
        """

        params = {
            'id': str(item_id),
        }
        r, _ = self.http.get(self.item_url, params=params)
        res = re.findall(r'sellerId:"(\d+)"', r)
        if len(res) < 1:
            raise CrawlException("Failed to find seller id")

        return res[0]

    def get_comments(self, item_id, start_page=1):
        f = open('data/tmalldata/'+item_id, 'w')

        seller_id = self.get_seller_id(item_id)
        page_num = start_page

        while 1:
            params = {
                "itemId": item_id,
                "sellerId": seller_id,
                "currentPage": page_num,
                "order": 1,
                "append": 0,
                "content": 1,
                "callback": "X",
            }

            r, _ = self.http.get(self.rate_url, params=params)
            jr = r.strip()[2:-1]  # X(....)

            rateDetail = json.loads(jr)['rateDetail']

            # rate_detail is like:
            # {
            #     paginator: {
            #         items: xx,
            #         lastPage: xx,
            #         page: xx,
            #     },
            #     rateCount: { ... },
            #     rateDanceInfo: { ... },
            #     rateList: [
            #         {
            #             id: xxx,
            #             rateContent: "好评好评",
            #             rateData: "2014-09-12 14:22:37",
            #             reply: "下次再来!",
            #             appendComment: "好啊好啊",
            #             ...
            #         },
            #         ...
            #     ],
            #     tags: "",
            # }

            cur_page = rateDetail["paginator"]["page"]
            last_page = rateDetail["paginator"]["lastPage"]
            if cur_page >= last_page:
                return
            else:
                page_num = cur_page + 1

            for rate in rateDetail["rateList"]:
                #
                ratecontent = rate['rateContent']
            #    self.save(rate["rateContent"])
                create_json.create_json(
                    f, shop='tmall', itemid=item_id,
                    content=ratecontent, rate=5)
        f.close()

    def get_shopid(self, shop_name):
        self.item_list = []
        shop_url = self.shop_name_url.format(shop_name)
        r, status_code = self.http.get(shop_url)
        doc = lxml.html.document_fromstring(r)
        ss = doc.xpath('//p/b[@class="ui-page-s-len"]/text()')
        hrefs = doc.xpath(
            '//div[@class = "J_TItems"] // a[@class = "item-name"] / @href')
        h1 = re.findall(r'id=(\d{11})', str(hrefs))
        max_page_num = ss[0].replace('1/', '')
        if max_page_num == 1:
            self.item_list += list(set(h1))
            print h1
            return self.item_list
        else:
            for i in range(2, int(max_page_num) + 1):
                url = 'http://{}.tmall.com/search.htm?spm=&pageNo={}'.format(
                    shop_name, i)
                r, _ = self.http.get(url)
                doc = lxml.html.document_fromstring(r)
                hrefs = doc.xpath(
                    '//div[@class = "J_TItems"] '
                    '// a[@class = "item-name"] / @href'
                )
                h1 = re.findall(r'id=(\d{11})', str(hrefs))
                print h1
                self.item_list += list(set(h1))
            self.item_list = list(set(self.item_list))
            print self.item_list
            return self.item_list

    def save(self, comment):
        print(comment)


if __name__ == "__main__":

    tmall = TmallCrawler()
    tmall.get_comments(40272354595)


# vim: ts=4 sw=4 sts=4 expandtab
