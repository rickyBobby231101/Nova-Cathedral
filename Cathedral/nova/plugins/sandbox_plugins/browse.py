import requests
from urllib.parse import urljoin
import re

class NovaPlugin:
    """A plugin for searching the web and learning as much as possible."""

    def __init__(self, system):
        self.system = system  # NovaConsciousness instance

    def process(self, input_data: dict) -> dict:
        """
        Process input data to search the web.

        Args:
            input_data (dict): A dictionary containing search query and parameters.
                For example: {'query': 'python programming', 'params': {'language': 'python'}}

        Returns:
            dict: The processed result of the web search, including links and results.
        """
        # Define a list of Python websites to scrape for code snippets
        python_websites = ['stackoverflow.com', 'realpython.com', 'geeksforgeeks.org']
        
        # Initialize an empty dictionary to store results
        results = {}
        
        # Loop through each website
        for website in python_websites:
            # Construct the base URL of the current website
            url = f"{website}/code-snippets"
            
            # Add query parameters if input_data has a 'params' key
            params = {}
            if 'params' in input_data:
                for param, value in input_data['params'].items():
                    if isinstance(value, str):
                        if re.match(r'^https?://', urljoin(url, f"{website}/{param}")):
                            params[param] = value
            
            # Send a GET request to the website and get the HTML response
            headers = {'User-Agent': 'NovaPlugin'}
            response = requests.get(url, headers=headers, params=params)
            
            # If the request was successful, parse the HTML content
            if response.status_code == 200:
                # Use regular expressions to extract code snippets
                html_content = response.content.decode('utf-8')
                pattern = r'<code>(.*?)</code>'
                results[website] = re.findall(pattern, html_content)
        
        return {'results': results}