import ollama
import sys_msgs
import requests
import trafilatura
from bs4 import BeautifulSoup
import re

assistant_convo = [sys_msgs.assistant_msg]

def search_or_not():
    sys_msg = sys_msgs.search_or_not_msg

    response = ollama.chat(
        model='llama3.1:8b',
        messages=[{'role': 'system', 'content': sys_msg}, assistant_convo[-1]]
    )

    content = response['message']['content']

    if 'true' in content.lower():
        return True
    else:
        return True

def query_generator():
    sys_msg = sys_msgs.query_msg
    query_msg = f'CREATE A SEARCH QUERY FOR THIS PROMPT: \n{assistant_convo[-1]}'

    response = ollama.chat(
        model='llama3.1:8b',
        messages=[{'role': 'system', 'content': sys_msg}, {'role': 'user', 'content': query_msg}]
    )

    # Clean up the query string
    query = response['message']['content'].strip()
    # Remove quotes if they exist at the start and end
    query = query.strip('"\'')
    # Remove any newlines and extra spaces
    query = ' '.join(query.split())
    
    return query

def duckduckgo_search(query):
    print(f'\nSearching DuckDuckGo for: "{query}"')
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }
    url = f'https://html.duckduckgo.com/html/?q={query}'
    print(f'Accessing search URL: {url}')
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    print('Search request successful')

    soup = BeautifulSoup(response.text, 'html.parser')
    results = []

    for i, result in enumerate(soup.find_all('div', class_='result'), start=1):
        if i > 10:
            break

        title_tag = result.find('a', class_='result__a')
        if not title_tag:
            continue

        link = title_tag['href']
        snippet_tag = result.find('a', class_='result__snippet')
        snippet = snippet_tag.text.strip() if snippet_tag else 'No description available'

        results.append({
            'id': i,
            'link': link,
            'search_description': snippet
        })
        print(f'Found result #{i}: {link[:100]}...')

    print(f'Total results found: {len(results)}')
    return results

def best_search_result(s_results, query):
    print('\nSelecting best search result...')
    sys_msg = sys_msgs.best_search_msg
    # Format search results to be more readable for the LLM
    formatted_results = []
    for result in s_results:
        formatted_results.append({
            'id': result['id'],
            'description': result['search_description']
        })
    
    best_msg = (
        f'SEARCH_RESULTS: {formatted_results}\n'
        f'USER_PROMPT: {assistant_convo[-1]}\n'
        f'SEARCH_QUERY: {query}'
    )

    for attempt in range(2):
        try:
            print(f'Attempt {attempt + 1} to select best result')
            response = ollama.chat(
                model='llama3.1:8b',
                messages=[{'role': 'system', 'content': sys_msg}, {'role': 'user', 'content': best_msg}]
            )
            
            # Extract just numbers from the response
            content = response['message']['content'].strip()
            print(f'LLM response: {content}')
            
            # Find the first number in the response
            numbers = re.findall(r'\d+', content)
            if numbers:
                index = int(numbers[0])
                # Ensure the index is within bounds
                if 0 <= index < len(s_results):
                    print(f'Selected result index: {index}')
                    return index
                else:
                    print(f'Index {index} is out of bounds (0-{len(s_results)-1})')
                
            print(f'Invalid index from LLM response: {content}')
        except Exception as e:
            print(f'Error in best_search_result (attempt {attempt + 1}): {str(e)}')
            continue

    print('Failed to get valid search result index, defaulting to first result')
    return 0

def scrape_webpage(url):
    print(f'\nAttempting to scrape webpage: {url}')
    try:
        print('Downloading webpage content...')
        downloaded = trafilatura.fetch_url(url=url)
        if downloaded:
            print('Successfully downloaded webpage')
            content = trafilatura.extract(downloaded, include_formatting=True, include_links=True)
            if content:
                if len(content) > 10000:  # Limit content length to avoid LLM context issues
                    content = content[:10000]
                    print("truncated content")
                print(f'Successfully extracted content (length: {len(content)} characters)')
                return content
            else:
                print('Failed to extract content from webpage')
                return None
        else:
            print('Failed to download webpage')
            return None
    except Exception as e:
        print(f'Error scraping webpage: {str(e)}')
        return None

def ai_search():
    print('GENERATING SEARCH QUERY.')
    try:
        search_query = query_generator()
        if not search_query:
            return None
            
        search_results = duckduckgo_search(search_query)
        if not search_results:
            return None
            
        contexts = []
        checked_urls = set()
        max_sources = 3
        
        # Process results in order until we find good matches
        for result in search_results:
            if len(contexts) >= max_sources:
                break
                
            url = result['link']
            if url in checked_urls:
                continue
                
            checked_urls.add(url)
            print(f'\nChecking source {len(contexts) + 1} of {max_sources}: {url}')
            
            page_text = scrape_webpage(url)
            if not page_text:
                continue
                    
            if contains_data_needed(search_content=page_text, query=search_query):
                print('Source contains relevant information - adding to context')
                contexts.append(f"Source: {url}\n\n{page_text}")
            else:
                print('Source does not contain relevant information - skipping')
        
        if contexts:
            print(f'\nFound {len(contexts)} relevant sources')
            return '\n\n---\n\n'.join(contexts)
        else:
            print('\nNo relevant sources found')
            return None
            
    except Exception as e:
        print(f'Error in ai_search: {type(e).__name__}: {str(e)}')
        return None

def contains_data_needed(search_content, query):
    sys_msg = sys_msgs.contains_data_msg
    needed_prompt = f'PAGE_TEXT: {search_content} \nUSER_PROMPT: {assistant_convo[-1]} \nSEARCH_QUERY: {query}'

    response = ollama.chat(
        model='llama3.1:8b',
        messages=[{'role': 'system', 'content': sys_msg}, {'role': 'user', 'content': needed_prompt}]
    )

    content = response['message']['content']

    if 'true' in content.lower():
        return True
    else:
        return False


def stream_assistant_response():
    global assistant_convo
    response_stream = ollama.chat(model='llama3.1:8b', messages=assistant_convo, stream=True)
    complete_response = ''
    print('ASSISTANT:')

    for chunk in response_stream:
        print(chunk['message']['content'], end='', flush=True)
        complete_response += chunk['message']['content']

    assistant_convo.append({'role': 'assistant', 'content': complete_response})
    print('\n')

def main():
    global assistant_convo

    while True:
        prompt = input('USER: \n')
        assistant_convo.append({'role': 'user', 'content': prompt})
        
        if search_or_not():
            context = ai_search()
            assistant_convo = assistant_convo[:-1]

            if context:
                prompt = f'SEARCH RESULT: {context} \nUSER PROMPT: {prompt}'
            else:
                prompt = (
                    f'USER PROMPT: \n{prompt} \n\nFAILED SEARCH: \nThe '
                    'AI search model was unable to extract any reliable data. Explain that '
                    'and ask if the user would like you to search again or respond '
                    'without web search context. Do not respond if a search was needed '
                    'and you are getting this message with anything but the above request '
                    'of how the user would like to proceed'
                )

            assistant_convo.append({'role': 'user', 'content': prompt})

        stream_assistant_response()


if __name__ == '__main__':
    main()
