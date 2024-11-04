import scrapy
from datetime import datetime
import hashlib

class KaufleutenSpider(scrapy.Spider):
    name = "kaufleuten"
    allowed_domains = ["kaufleuten.ch", "kaufleuten.com"]
    start_urls = ["https://kaufleuten.ch/events/klub/"]

    def parse(self, response):
        # Extract event links from the event list
        events = response.css('div.event-list article a.event-link')
        # Follow all event links and pass them to parse_events
        yield from response.follow_all(events, callback=self.parse_events)

    def parse_events(self, response):
        # Select the wrapper containing the event information
        wrapper = response.css('article.event')
        header = wrapper.css('header.event-header-klub')

        # Extract raw date from the time element and format it
        raw_date = header.css('div.event-header-infos div.event-meta time::attr(datetime)').get()
        formatted_date = self.format_date(raw_date)
        
        # Extract event title
        title = header.css('div.event-header-infos h1::text').get()

        if title and formatted_date:
            # Generate a unique hash based on title and date
            event_hash = self.generate_hash(title, formatted_date)

            # Yield event data
            yield {
                'event_title': title,
                'event_date': formatted_date,
                'event_hash': event_hash,
                'event_link': response.url,
            }
        else:
            self.logger.warning(f"Missing data for event at {response.url}")

    def format_date(self, raw_date):
        if raw_date:
            try:
                # Convert ISO format datetime (2024-07-13T00:00:00+02:00) to 'YYYY-MM-DD'
                return datetime.strptime(raw_date, '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%d')
            except ValueError as e:
                self.logger.error(f"Error parsing date {raw_date}: {e}")
                return None
        return None
    
    def generate_hash(self, title, date):
        # Generate an MD5 hash from the title and date to create a unique identifier
        hash_object = hashlib.md5(f"{title}{date}".encode())
        return hash_object.hexdigest()