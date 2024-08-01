from django.shortcuts import render
import requests
from bs4 import BeautifulSoup

def scrape_infyz_website():
    url = 'https://www.infyz.com/'
    response = requests.get(url)
    if response.status_code != 200:
        return None, []
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract paragraphs
    paragraphs = soup.find_all('p')
    content = ' '.join([p.get_text() for p in paragraphs])
    
    # Extract image URLs
    images = []
    for img in soup.find_all('img'):
        img_url = img.get('src')
        if img_url:
            # Handle relative URLs
            if img_url.startswith('/'):
                img_url = url + img_url
            images.append(img_url)
    
    return content, images

# Load the scraped data
data, images = scrape_infyz_website()

def search_data(query):
    if not data:
        return "No data available.", [], True
    start_idx = data.lower().find(query.lower())
    if start_idx == -1:
        return "No relevant information found.", [], True
    
    # Define the snippet length
    snippet_length = 700
    start_idx = max(start_idx - snippet_length // 2, 0)
    end_idx = min(start_idx + snippet_length, len(data))
    snippet = data[start_idx:end_idx]

    # Make sure to include the query term in the snippet
    snippet = snippet.replace(query, f"<strong>{query}</strong>")
    
    return snippet + "...", images, False


def index(request):
    response = ""
    found_images = []
    no_results = False
    if request.method == 'POST':
        query = request.POST.get('query')
        response, found_images, no_results = search_data(query)
    return render(request, 'index.html', {'response': response, 'found_images': found_images, 'no_results': no_results})
