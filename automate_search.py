import os
import json
import re
from flask import Flask, render_template, request, jsonify
from serpapi import GoogleSearch

# Flask app setup
app = Flask(__name__)

# SerpAPI configuration
SERP_API_KEY = "f67f23d88d15c0b6e1c598655087ffc286b474bd68a5e86ea42a20de35e7ac23"
output_json_path = "./generalized_fetched_details.json"

# Function to extract email addresses from text
def extract_email(text):
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    return re.findall(email_pattern, text)

# Function to perform Google search
def google_search(query, num_results=10):
    search = GoogleSearch({"q": query, "num": num_results, "api_key": SERP_API_KEY})
    results = search.get_dict()
    return results.get("organic_results", [])

# Step 1: Search for a list of companies
def search_companies(query):
    print(f"\nSearching for companies related to: {query}")
    search_results = google_search(query)
    
    companies = []
    for result in search_results:
        title = result.get("title", "No Title")
        if title:
            companies.append(title.split("-")[0].strip()) 
    return list(set(companies))  

# Step 2: Search for key individuals and extract emails
def search_key_individuals(company):
    print(f"\nSearching for key individuals in: {company}")
    query = f"{company} CEO, CTO, HR contact details, LinkedIn"
    search_results = google_search(query)
    
    key_individuals = {"Company": company, "Details": []}
    
    for result in search_results:
        title = result.get("title", "No Title")
        link = result.get("link", "No Link")
        snippet = result.get("snippet", "No Snippet")
        
        # Extract emails from the title and snippet
        emails_from_title = extract_email(title)
        emails_from_snippet = extract_email(snippet)
        
        details = {
            "Title": title,
            "Link": link,
            "Snippet": snippet,
            "Emails": list(set(emails_from_title + emails_from_snippet))  # Combine and deduplicate emails
        }
        
        if details:
            key_individuals["Details"].append(details)
    
    return key_individuals

# Function to save results to JSON file
def save_to_json(data, file_path):
    try:
        with open(file_path, "w", encoding="utf-8") as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=4)
        print(f"\nExtracted details saved to {file_path}")
    except Exception as e:
        print(f"Error writing to JSON file: {e}")

# Route for the home page
@app.route('/')
def home():
    return render_template('index.html')

# Route to process the queries
@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    if not query:
        return jsonify({"error": "Query is required"}), 400
    
    all_results = []
    
    companies = search_companies(query)
    print(f"\nCompanies found: {companies}")
    
    for company in companies:
        key_individuals = search_key_individuals(company)
        if key_individuals["Details"]:
            all_results.append(key_individuals)
    
    save_to_json(all_results, output_json_path)
    
    return jsonify(all_results)

@app.route('/download')
def download():
    return jsonify({"download_link": output_json_path})

if __name__ == '__main__':
    app.run(debug=True)
