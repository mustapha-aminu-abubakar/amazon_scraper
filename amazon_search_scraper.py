import pandas as pd                     #for wrangling data
import requests                         #for making http requests to target server
import re                               #for regex operations   
import numpy as np                      #for wrangling data
from datetime import datetime as dt     #for date/time operations                         
from bs4 import BeautifulSoup as bs     #for parsing http response


http_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36", 
            "Accept-Language": "en-US,en;q=0.9"
           }
    

def generate_search_keywords():
    """
    Prompts user for search keywords

    Returns:
        list: [*keywords]
    """
    
    keywords = []
    while True:
        keyword = input("Please enter search keyword (Press enter to submit):   ")
        if len(keyword) > 0: keywords.append(keyword) 
        else: break
    print('\n', "Search keywords: ", ', '.join(keywords), '\n', sep='')
    return keywords



def generate_search_results(keywords: list):
    """
    Function generates url path(s) to results of search keyword(s) 

    Args:
        keywords (list): contains search keyword(s)

    Returns:
        dict: ({keyword: url})
    """
    
    input("\n<<<   Generate search result urls    >>> \n")
    
    results = {keyword: f"https://www.amazon.com/s?k={keyword}&ref=nb_sb_noss" for keyword in keywords}
    print("Search result urls:", *list(results.values()), '', sep='\n    ')
    return results



def generate_links(results: list):
    """
    Generate the n number of urls, for each keyword.
    N is the number of pages in the pagination strip

    Args:
        results (list): url of search result

    Returns:
        dict: {keyword_n: url}
    """
    
    input("\n<<<    Identify pagination element, extract page url from each item    >>>\n")
    
    links = {}
    for result in results:
        page = requests.get(results[result], headers=http_headers)   #makes http request
        soup = bs(page.content, 'html.parser')                  #parses http response
        
        pages = soup.find_all('span', class_= 's-pagination-item')                      #locates pagination element
        pages_num = max([int(page.text) for page in pages if page.text.isdigit()])      #identifies number of pages   
        pages_link_template = soup.find('a', class_= 's-pagination-item').get('href')   #extracts page's hyperlink from 'href' attribute
        pages_link_num = re.search(r"&page=(\d+)", pages_link_template)                 #locates page number argument within hyperlink using regex
        
        #replaces page number argument with hyperlink with numbers ranging 1 <= x <= pages_num 
        for i in range(1, pages_num + 1):                                               
            links["{0}_{1}".format(result, i)] = "https://www.amazon.com{}".format(pages_link_template.replace(pages_link_num.group(1), str(i))) 
        
        print("Pages to be scraped : ", *list(links.values()), '', sep="\n  " )
        
    return links



def scrape_links(links: dict):
    """
    Webscrapes each of the supplied urls and parses relevant product information.

    Args:
        links (dict): list of urls to be scraped.

    Returns:
        pd.DataFrame: collection of products and relevant information.
    """
    
    input(f"\n<<<    Begin scraping, number of pages: {len(links)}    >>>\n")
    
    cols = ['keyword', 'title', 'sale_price($)', 'anchor_price($)', 
            'ratings(5)', 'reviews', 'orders', 'scrape_datetime']  #product information
    df = pd.DataFrame(columns=cols)                                         #initializing dataframe object 
    
    for link in links:
        try:
            response = requests.get(links[link], headers=http_headers)           #making http request for url resource
        except:
            print(links[links], 'get request failed')
            return None
        
        soup = bs(response.content, "html.parser")                          #parsing http request
        products = soup.find_all('div', class_='puis-card-container')
        
        for product in products:
            try:
                title = product.find('span', class_="a-color-base").text    #extracting product title
            except:
                title = ''
            
            try:
                ratings = product.find('span', class_="a-icon-alt").text    #extracting product rating
                ratings = ratings.split(" out")[0]
            except:
                ratings = ''
                
            try:
                rating_cnt = product.find('span', class_="a-size-base s-underline-text").text       #extracting product review count
                rating_cnt = rating_cnt.replace(",","")
            except:
                rating_cnt = ''
                
            try:
                purchase_cnt = product.find('span', class_="a-size-base a-color-secondary").text    #extracting product order count
                purchase_cnt = purchase_cnt.split(' bought')[0]
                purchase_cnt = purchase_cnt.replace('K', '000')
            except:
                purchase_cnt = ''
                
            try:
                price_whole = product.find('span', class_ = 'a-price-whole').text                   #extracting product sale price
                price_fraction = product.find('span', class_='a-price-fraction' ).text
                price = price_whole + price_fraction
            except:
                price = ''
            
            try:
                old_price = product.find('span', class_ = 'a-offscreen').text                       #extracting product anchor price
                old_price = old_price.split('$')[-1]
            except:
                old_price = ''
            
            product_info = [link.split('_')[0], title, price, 
                            old_price, ratings, rating_cnt, 
                            purchase_cnt, dt.now().strftime("%Y-%m-%d %H:%M:%S")]                  #adding product info to dataframe
            df.loc[len(df)] = product_info
            
            print(product_info)
    return df

def save_dataframe(dframe, filename: str):
    
    input("\n<<<    Clean and save webscrape data into csv file    >>>\n")

    df = dframe.copy()    #making a backup of dataframe 
    
    num_cols = [col for col in df.columns if col not in ['keyword', 'title', 'orders', 'scrape_datetime']]             #highlighting numerical attributes
    for col in num_cols:                            #parsing numerical attributes
        df[col] = (
                        df[col]
                        .astype(str)                # Convert all values to strings
                        .replace('', np.nan)        # Replace empty strings with NaN
                        .str.replace(',', '')       # Remove thousand separators
        .astype(float) 
        )
        
    df['orders'] = df['orders'].map(lambda x: x if x.endswith('+') else np.nan)                     #standardizing orders attribute
    
    df.to_csv(filename, index=None)                    #downloading dataframe into csv file
    
    print(f"{filename} file successfully created", f"{len(df)} products scraped", '', sep='\n')






keywords = generate_search_keywords()
results = generate_search_results(keywords)
links = generate_links(results)
webscrape = scrape_links(links)
save_dataframe(webscrape, '_'.join(keywords)+'.csv')






