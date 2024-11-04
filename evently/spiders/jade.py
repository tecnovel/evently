import scrapy
from datetime import datetime
import hashlib

class JadeSpider(scrapy.Spider):
    name = "jade"
    allowed_domains = ["jade.ch"]
    start_urls = ["https://www.jade.ch/events"]

    def parse(self, response):
        # Extract all event links from the event list
        events = response.css('div.eventList article a.lightboxLink')
        # Follow each event link and parse event details
        yield from response.follow_all(events, callback=self.parse_event_details)

    def parse_event_details(self, response):
        # Extracting wrapper containing event information
        wrapper = response.css('div.slideWrapper')

        # Extracting raw date and formatting it
        raw_date = wrapper.css('p.title5::text').get()
        formatted_date = self.format_date(raw_date)

        # Extracting event title
        title = wrapper.css('h2.title1::text').get()

        if title and formatted_date:
            # Generate a unique hash based on the title and date
            event_hash = self.generate_hash(title, formatted_date)

            # Yield event details
            yield {
                'title': title,
                'date': formatted_date,
                'hash': event_hash,
                'event_link': response.url,
            }
        else:
            # Log a warning if any crucial information is missing
            self.logger.warning(f"Missing title or date for event at {response.url}")

    def format_date(self, raw_date):
        if raw_date:
            try:
                # Converting date from '13. July 2024' to '2024-07-13'
                return datetime.strptime(raw_date.strip(), '%d. %B %Y').strftime('%Y-%m-%d')
            except ValueError as e:
                self.logger.error(f"Error parsing date '{raw_date}': {e}")
                return None
        return None
    
    def generate_hash(self, title, date):
        # Generate a unique MD5 hash based on the title and date
        if title and date:
            hash_object = hashlib.md5(f"{title}{date}".encode())
            return hash_object.hexdigest()
        return None