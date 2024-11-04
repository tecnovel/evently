import scrapy
from datetime import datetime
import hashlib

class HiveclubSpider(scrapy.Spider):
    name = "hiveclub"
    allowed_domains = ["hiveclub.ch"]
    start_urls = ["https://hiveclub.ch/hive/"]

    def parse(self, response):
        # Loop through all event items
        events = response.css('div.view-item-calendar')
        
        for event in events:
            # Extract event link
            event_link = event.css('a::attr(href)').get()
            event_link = response.urljoin(event_link)
            
            # Extract event date
            date_str = event.css('span.date-display-single::attr(content)').get()
            
            # Convert date string to datetime object
            if date_str:
                event_date = self.format_date(date_str)
                current_date = datetime.now().date()

                # Check if the event date is in the future
                if event_date and event_date >= current_date:
                    # Follow the event link to extract event details
                    yield response.follow(event_link, callback=self.parse_event_details, meta={'event_date': event_date})

    def parse_event_details(self, response):
        # Extract event name
        event_name = response.css('h2::text').get()

        # Extract event date passed from the previous request
        event_date = response.meta.get('event_date')

        # Extract event time (if available)
        event_time = response.css('div.field-name-field-time .field-item::text').get()

        if event_name and event_date:
            # Generate a unique hash for the event
            event_hash = self.generate_hash(event_name, event_date)

            # Yield the event details
            yield {
                'event_title': event_name,
                'event_date': event_date,
                'event_time': event_time,
                'event_link': response.url,
                'event_hash': event_hash,
            }
        else:
            self.logger.warning(f"Missing event name or date for event at {response.url}")

    def format_date(self, date_str):
        try:
            # Convert ISO format datetime (e.g., '2024-07-13T00:00:00+02:00') to 'YYYY-MM-DD'
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z").date()
        except ValueError as e:
            self.logger.error(f"Error parsing date '{date_str}': {e}")
            return None

    def generate_hash(self, title, date):
        # Generate a unique MD5 hash from the event title and date
        hash_object = hashlib.md5(f"{title}{date}".encode())
        return hash_object.hexdigest()