import logging
from django.http import HttpResponse
from django.shortcuts import render
from core.forms import URLForm, HunterEmailForm, SearchForm
from googlesearch import search
import requests
from bs4 import BeautifulSoup
import re
import csv
from core.models import Configurations
from django.views.decorators.csrf import csrf_exempt

# Configure logging
logger = logging.getLogger(__name__)

config = Configurations.objects.first()
HUNTER_API_KEY = config.config.get('hunter_api_key')

def get_emails_from_hunter(domain):
    url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={HUNTER_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for HTTP errors
        data = response.json().get('data', {})
        emails = [email['value'] for email in data.get('emails', [])]
        return emails
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching emails from Hunter.io: {e}")
        return []

def extract_emails(text):
    return set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text))

def is_social_or_company_link(link):
    social_media_keywords = ['facebook', 'twitter', 'instagram', 'linkedin']
    company_keywords = ['about', 'service', 'products', 'careers', 'contact']

    link_lower = link.lower()
    if any(keyword in link_lower for keyword in social_media_keywords):
        return True
    if any(keyword in link_lower for keyword in company_keywords):
        return True
    return False

def get_contact_info(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for HTTP errors
        soup = BeautifulSoup(response.text, 'html.parser')

        emails = extract_emails(response.text)

        links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith('http')]
        social_and_company_links = [link for link in links if is_social_or_company_link(link)]

        linkedin_profiles = [link for link in social_and_company_links if 'linkedin.com' in link]
        company_links = [link for link in social_and_company_links if 'linkedin.com' not in link]

        company_name = soup.title.string if soup.title else 'No title found'

        return {
            'url': url,
            'emails': list(emails),
            'linkedin_profiles': linkedin_profiles,
            'company_links': company_links,
            'company_name': company_name,
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error scraping contact info from {url}: {e}")
        return {
            'url': url,
            'emails': [],
            'linkedin_profiles': [],
            'company_links': [],
            'company_name': 'N/A',
        }

def add_hunter_emails(info):
    domain = re.findall(r'://([^/]+)', info['url'])[0]
    hunter_emails = get_emails_from_hunter(domain)
    info['emails'].extend(hunter_emails)
    return info

def scrape_websites(urls, include_hunter_emails=False):
    results = []
    for url in urls:
        info = get_contact_info(url)
        if include_hunter_emails:
            info = add_hunter_emails(info)
        results.append(info)
    return results

def google_search(query):
    try:
        search_results = search(query, num_results=20, lang='en')
        return search_results
    except Exception as e:
        logger.error(f"Error performing Google search: {e}")
        return []

def scrape_company_data(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise exception for HTTP errors
        soup = BeautifulSoup(response.content, 'html.parser')
        company_name_element = soup.find('h1')
        company_name = company_name_element.text.strip() if company_name_element else "N/A"
        return {
            'company_name': company_name,
            'url': url
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error scraping company data from {url}: {e}")
        return {
            'company_name': 'N/A',
            'url': url
        }

def scrape_clutch_data(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise exception for HTTP errors
        soup = BeautifulSoup(response.content, 'html.parser')
        
        company_name_element = soup.find('h1', class_='provider-info__name')
        company_name = company_name_element.text.strip() if company_name_element else "N/A"
        
        website_element = soup.find('a', class_='provider-website-link')
        website_link = website_element['href'] if website_element else "N/A"

        contact_info_element = soup.find('div', class_='text-secondary')
        contact_info = contact_info_element.text.strip() if contact_info_element else "N/A"

        return {
            'company_name': company_name,
            'url': url,
            'website_link': website_link,
            'contact_info': contact_info
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error scraping clutch data from {url}: {e}")
        return {
            'company_name': 'N/A',
            'url': url,
            'website_link': 'N/A',
            'contact_info': 'N/A'
        }

def save_to_csv(data):
    keys = ['url', 'emails', 'linkedin_profiles', 'company_links', 'company_name']
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="scraped_data.csv"'
    writer = csv.DictWriter(response, fieldnames=keys)

    writer.writeheader()
    for row in data:
        writer.writerow({
            'url': row['url'],
            'emails': ', '.join(row['emails']),
            'linkedin_profiles': ', '.join(row['linkedin_profiles']),
            'company_links': ', '.join(row['company_links']),
            'company_name': row['company_name'],
        })
    return response

@csrf_exempt
def scrape_view(request):
    url_form = URLForm()
    hunter_email_form = HunterEmailForm()
    search_form = SearchForm()
    scraped_data = None
    hunter_emails = None

    if request.method == 'POST':
        if 'scrape' in request.POST:
            url_form = URLForm(request.POST)
            if url_form.is_valid():
                urls = url_form.cleaned_data['urls'].split()
                include_hunter_emails = 'include_hunter_emails' in request.POST
                scraped_data = scrape_websites(urls, include_hunter_emails=include_hunter_emails)
                request.session['scraped_data'] = scraped_data  # Store data in session for download

        elif 'hunter' in request.POST:
            hunter_email_form = HunterEmailForm(request.POST)
            if hunter_email_form.is_valid():
                domain = hunter_email_form.cleaned_data['domain']
                hunter_emails = get_emails_from_hunter(domain)

        elif 'search' in request.POST:
            search_form = SearchForm(request.POST)
            if search_form.is_valid():
                department = search_form.cleaned_data['department']
                location = search_form.cleaned_data['location']
                query = f'{department} companies in {location}'
                search_results = google_search(query)
                scraped_data = [scrape_company_data(result) for result in search_results]
                request.session['scraped_data'] = scraped_data

        elif 'clutch' in request.POST:
            search_form = SearchForm(request.POST)
            if search_form.is_valid():
                department = search_form.cleaned_data['department']
                location = search_form.cleaned_data['location']
                query = f'{department} companies in {location}'
                search_results = google_search(query)
                scraped_data = [scrape_clutch_data(result) for result in search_results]
                request.session['scraped_data'] = scraped_data

    return render(request, 'scrape.html', {
        'url_form': url_form,
        'hunter_email_form': hunter_email_form,
        'search_form': search_form,
        'scraped_data': request.session.get('scraped_data', None),
        'hunter_emails': hunter_emails,
    })

def download_csv(request):
    data = request.session.get('scraped_data', [])
    return save_to_csv(data)
