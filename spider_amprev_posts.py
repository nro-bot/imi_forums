import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.crawler import CrawlerProcess
import logging
from scrapy.utils.log import configure_logging 

import numpy as np
import pandas as pd
# self.logger.info("Visited %s", response.url)

# for a given category 
# e.g. https://ampreviews.net/index.php?forums/discussion-pittsburgh.89/

# https://ampreviews.net/index.php?threads/lin-spa-brownsville-rd.133397/

class PostSpider(CrawlSpider):
    configure_logging(install_root_handler=False)
    logging.basicConfig(
        filename='log.txt',
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%d/%b/%Y %H:%M:%S',
        level=logging.INFO # NOTE: doesn't actually do anything
    )
    name = 'extract_posts'

    def start_requests(self):
        self.base_url = 'https://ampreviews.net'

        post_url = '/index.php?threads/building-a-list-of-he-only-spots-in-manhattan.129971/' 
        url = self.base_url + post_url 
        self.logger.error(f'now working with url {url}')
        yield scrapy.Request(url=url, callback=self.parse_page)

    def parse_page(self, response):
        page_name_and_pagination = response.css('title::text').get() # e.g. Discussion-Dallas | Page 2 | AMPReviews
        max_pages = response.css('li.pageNav-page:last-child a::text').get()
        page_url = response.url  
        page_name = response.css('.p-title-value::text').get()


        # - get post metadata
        posts = response.css('article.message--post')
        self.logger.error('hi')
        for post in posts: 
            post_id = post.css('::attr(data-content)').get()
            # NOTE unclosed parenthesis #ERROR:  
            # cssselect.parser.SelectorSyntaxError: Expected an argument, got <EOF at 18>

            # example link: "/index.php?threads/building-a-list-of-he-only-spots-in-manhattan.129971/post-954437" 
            
            # -- POST STATS
            self.logger.error('hi?')
            posted_date_readable = post.css('.message-date time::attr(title)').get()
            posted_date_data = post.css('.message-date time::attr(title)').get()
            post_ordinal = post.css('.message-attribution-opposite a::text').get() # example: #19 
            post_ordinal = post_ordinal[1:] if post_ordinal else None # in case CSS selector fails / website changes, scraper so not completely fail


            # -- POST TEXT 
            self.logger.error('hi2')
            post_text = ''.join(post.css('div.bbWrapper::text').getall())

            # -- QUOTES: handle quotes if exist
            quotes = post.css('div.bbCodeBlock--quote')
            num_quotes = len(quotes) # store as checksum in case want to unconcatenate quotes

            self.logger.error('hi3')
            quoted_post_ids = []
            quoted_authors = []
            quoted_contents = []
            if quotes: 
                for quote in quotes:
                    # example output: <a href="/index.php?goto/post&amp;ipostd=955852" class="bbCodeBlock-sourceJump" data-xf-click="attribution" data-content-selector="#post-955852">XYZ said:</a>
                    quoted_post_id = quote.css('.bbCodeBlock-sourceJump::attr(data-content-selector)').get()
                    quoted_author = quote.css('a::text').get()  #.replace(' said:', '')
                    quoted_author = quoted_author.split()[0] if quoted_author else None
                    quoted_post_content = quote.css(
                        '.bbCodeBlock-expandContent::text').get()   

                    quoted_authors.append(quoted_author)
                    quoted_post_ids.append(quoted_post_id)
                    quoted_contents.append(quoted_post_content)
                ' ~!~ '.join(quoted_post_ids) 
                ' ~!~ '.join(quoted_authors) 
                ' ~!~ '.join(quoted_contents) 
                
            # --  LIKES
            self.logger.error('hi3')
            likers = post.css('div.likesBar a * ::text').getall()
            num_likers = len(likers) # could be interesting stat
            likers = ' - '.join(likers)

            # -- AUTHOR STATS
            self.logger.error('hi4')
            author = post.css('::attr(data-author)').get()
            author_url = post.css('a.username::attr(href)').get()
            author_title, author_num_posts, author_num_reviews = None, None, None 
            try:
                author_title, author_num_posts, author_num_reviews = post.css(
                    '.userTitle ::text').getall()[:3]
                    # Example output: ['Review Contributor', 'Messages: 46', 'Reviews: 13',# 'Joined ', 'Oct 2, 2019']
                author_num_posts = author_num_posts.split()[-1]
                author_num_reviews = author_num_reviews.split()[-1]
            except: # May produce indexing error if no results
                self.logger.error('Attempt to extract author stats failed')

            join_date_readable = post.css('.userTitle time::attr(title)').get()
            join_date_data  = post.css('.userTitle time::attr(data-time)').get()

            self.logger.info(f'Now scraped: {page_name_and_pagination} -- {page_url} -- TotalPages {max_pages}')

            # -- YIELD
            self.logger.error('hi yield')
            # create dictionary to yield
            loc = locals()
            self.logger.debug(post_id)
            fields = '''
                post_id
                post_text
                posted_date_readable
                posted_date_data 
                post_ordinal
                post_text

                author
                author_url
                author_title 
                author_num_posts 
                author_num_reviews
                join_date_readable
                join_date_data

                quoted_post_ids
                quoted_authors
                quoted_contents
                num_quotes
                likers
                num_likers 
            '''.split()

            fields = '''
                post_id
            '''.split()
            #fields = [field.strip() for field in fields]
            fields = set(fields) # prevent dup key error
            self.logger.debug(fields)

            page_data = {key: loc[key] for key in loc.keys() if key in fields}
            page_data['comment'] = page_name

            yield page_data

'''
        # dirty hack to insert "comment" into bottom of csv file
        # which contains the current page and url, just in case
        self.logger.error('hi yield final')
        yield {
            'comment': f'{page_name_and_pagination} -- {page_url} -- TotalPages {max_pages}'
        }

        next_page = response.css('a.pageNav-jump--next::attr(href)').get()
        self.logger.error('hi nextPAge')
        if next_page is not None:
            next_page = response.urljoin(next_page)
            self.logger.info(f'going to next page: {next_page}')
            yield scrapy.Request(next_page, callback=self.parse_page)
'''

c = CrawlerProcess(
    settings={
        "FEEDS":{
            "_tmp_threads.csv" : {"format" : "csv",
                                "overwrite":True,
                                "encoding": "utf8",
                            }},
        "CONCURRENT_REQUESTS":1, # default 16
        "CONCURRENT_REQUESTS_PER_DOMAIN":1, # default 8 
        "CONCURRENT_ITEMS":1, # DEFAULT 100
        "DOWNLOAD_DELAY": 3, # default 0
        "DEPTH_LIMIT":1,
        #"JOBDIR":'crawls/amprev_posts',
        #"DUPEFILTER_DEBUG":True,
    }
)

    #'USER_AGENT': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36',
    #'CLOSESPIDER_PAGECOUNT': 3,
c.crawl(PostSpider)
c.start()