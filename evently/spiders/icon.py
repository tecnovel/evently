import scrapy
from datetime import datetime
import hashlib
from scrapy.selector import Selector
import json
import re

class IconZurichSpider(scrapy.Spider):
    name = "icon_zurich"
    allowed_domains = ["icon-zurich.ch"]
    start_urls = ['https://icon-zurich.ch/wp-json/wp/v2/pages/4339']

    def parse(self, response):
        data = json.loads(response.text)
        html_content = data.get('content', {}).get('rendered', '')
        selector = Selector(text=html_content)
        
        # Extract event details
        events = self.extract_events(selector)
        
        for event in events:
            # Process each event
            yield event

    def extract_events(self, selector):
        events = []
        # Find all rs-slide elements
        slides = selector.xpath('//rs-slide')
        
        for slide in slides:
            event = {}
            
            # Extract date
            date_text = slide.xpath('.//rs-layer[contains(@id, "layer-23") or contains(@id, "layer-25") or contains(@id, "layer-0")]/text()').get()
            date = self.format_date(date_text)
            event['date'] = date
            
            # Extract time
            time_text = slide.xpath('.//rs-layer[contains(@id, "layer-19") or contains(@id, "layer-26") or contains(@id, "layer-20")]/text()').get()
            event['time'] = time_text.strip() if time_text else None
            
            # Extract event name from background image filename
            bg_elem_style = slide.xpath('.//rs-bg-elem/@style').get()
            event_name = None
            if bg_elem_style:
                # Extract the URL from the style attribute
                match = re.search(r"url\('(.*?)'\)", bg_elem_style)
                if match:
                    image_url = match.group(1)
                    # Extract the filename
                    filename = image_url.split('/')[-1]
                    # Remove file extension and replace underscores with spaces
                    event_name = filename.rsplit('.', 1)[0].replace('_', ' ')
                    event_name = event_name.strip()
            
            # If event name not found, use day or other text as a fallback
            if not event_name:
                name_text = slide.xpath('.//rs-layer[contains(@id, "layer-16") or contains(@id, "layer-17")]/text()').get()
                if name_text:
                    event_name = name_text.strip()
                else:
                    # Combine day and DJ's name as a last resort
                    day_text = slide.xpath('.//rs-layer[contains(@id, "layer-16") or contains(@id, "layer-0")]/text()').get()
                    dj_name = slide.xpath('.//rs-layer[contains(@id, "layer-14") or contains(@id, "layer-15") or contains(@id, "layer-24") or contains(@id, "layer-25")]/text()').get()
                    if day_text and dj_name:
                        event_name = f"{day_text.strip()} - {dj_name.strip()}"
            
            event['name'] = event_name
            
            # Generate a unique hash ID
            if event['date'] and event['name']:
                event_id = f"{event['date']}_{event['name']}"
                event_hash = hashlib.md5(event_id.encode()).hexdigest()
                event['id'] = event_hash
                events.append(event)
            
        return events

    def format_date(self, raw_date):
        if raw_date:
            try:
                # Adjusted date format to match 'dd.mm.yyyy'
                return datetime.strptime(raw_date.strip(), '%d.%m.%Y').strftime('%Y-%m-%d')
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