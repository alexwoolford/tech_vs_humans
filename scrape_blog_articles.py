import json
import re
import time
from datetime import datetime

import requests
import requests_cache
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta

# Setting up logging
import logging

logging.basicConfig(filename='scrape_blog_articles.log', level=logging.DEBUG)

requests_cache.install_cache()
requests_cache.install_cache(expire_after=86400)  # Cache expires after 1 day


# ------------------
# HTTP Utilities
# ------------------
def get_html(url: str) -> str:
    try:
        if not requests_cache.get_cache().contains(url):
            time.sleep(10)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Could not fetch URL {url}: {e}")
        return ""

    return response.text


# ------------------
# Parsing Utilities
# ------------------
def extract_article_urls(html_content: str) -> list[str]:
    soup = BeautifulSoup(html_content, 'html.parser')

    # Pattern to match the article URL format
    pattern = re.compile(r'https://techvshumans\.com/blog/\d{4}/\d{2}/\d{2}/[\w\-]+/')

    article_urls = [a['href'] for a in soup.find_all('a', href=pattern)]
    return list(set(article_urls))


def parse_article(html_content: str) -> dict:
    soup = BeautifulSoup(html_content, 'html.parser')

    try:
        title = soup.find('h1', class_='entry-title').text.strip()
    except AttributeError:
        title = "Not found"
        logging.error("Could not find article title")

    try:
        author = soup.find('span', class_='author vcard').text.strip()
    except AttributeError:
        author = "Not found"
        logging.error("Could not find article author")

    try:
        content = soup.find('div', class_='entry-content').text.strip()
    except AttributeError:
        content = "Not found"
        logging.error("Could not find article content")

    return {
        'title': title,
        'author': author,
        'content': content
    }


# ------------------
# URL Utilities
# ------------------
def create_month_urls(dates: list[datetime]):
    base_url = "https://techvshumans.com/blog/"
    urls = []
    for date in dates:
        url = f"{base_url}{date.strftime('%Y/%m/')}"
        urls.append(url)

    return urls


def generate_monthly_dates(start_date: datetime, end_date: datetime) -> list[datetime]:
    dates = []
    current_date = start_date

    while current_date <= end_date:
        dates.append(current_date)
        current_date += relativedelta(months=1)

    return dates


# ------------------
# Main Execution
# ------------------
if __name__ == "__main__":
    start_date = datetime(2020, 2, 1)
    end_date = datetime(2023, 9, 1)
    dates = generate_monthly_dates(start_date, end_date)
    month_urls = create_month_urls(dates)
    articles = []
    for month_url in month_urls:
        html_content = get_html(month_url)
        article_urls = extract_article_urls(html_content)

        for article_url in article_urls:
            article_record = parse_article(get_html(article_url))
            article_record['url'] = article_url
            articles.append(article_record)

    with open('articles.jsonl', 'w', encoding='utf-8') as file:
        for article in articles:
            json.dump(article, file, ensure_ascii=False)
            file.write('\n')
