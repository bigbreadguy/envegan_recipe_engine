import os
import time
import json
import random
import tqdm
import argparse

import requests
from bs4 import BeautifulSoup

def get_response(url:str):
    user_agents = [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 13_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; U; Android 2.2) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
        "Mozilla/5.0 (Linux; Android 10; Android SDK built for x86) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 7.1.2; AFTMM Build/NS6265; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/70.0.3538.110 Mobile Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"]

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9", 
        "Accept-Encoding": "gzip, deflate", 
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8", 
        "Dnt": "1", 
        "Host": "httpbin.org", 
        "Upgrade-Insecure-Requests": "1", 
        "User-Agent": user_agents[random.randrange(len(user_agents))], 
    }
    
    response = requests.get(url)

    return response

def crawl_review_article(url:str):
    response = get_response(url)
    soup = BeautifulSoup(response.content, "html.parser", from_encoding="utf-8")

    article = soup.find_all(class_="entry-content")[0]
    paragraphs = article.find_all("p")

    text = ""
    for p in paragraphs:
        t = p.get_text()
        text+=t+" "

    ext = (".jpg", ".jpeg", ".png")

    images = []
    for p in paragraphs:
        links = p.find_all("a")
        for link in links:
            ref = link.get("href")
            if ref.endswith(ext):
                images.append(ref)
        
        try:
            imgs = p.find_all("img")
            for img in imgs:
                images.append(img.get("src"))
        except:
            pass
    
    return text, images

def list_up_reviews(url:str):
    response = get_response(url)
    soup = BeautifulSoup(response.content, "html.parser", from_encoding="utf-8")

    reviews = soup.find_all(class_="entry-content")[0]
    articles = reviews.find_all("li")

    result = {}
    for idx, a in enumerate(articles):
        title = a.get_text()
        if title == "Share":
            break

        link = a.find("a")
        if link is None:
            link = a.find("span").find("a")

        ref = link.get("href")

        result[idx] = {"title" : title, "url" : ref}
    
    return result

def parse_title(title:str):
    splt = title.split(":")

    place = splt[0]
    score = splt[1][1:3]
    
    starcount = title.count("*")
    isfull = starcount==1

    if score == "UN":
        score = "unrated"

    return place, score, isfull

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="crawl a review blog",
                                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--url", type=str, dest="url", help="target url")
    parser.add_argument("--title", type=str, dest="title", help="target title")
    args = parser.parse_args()

    reviews = list_up_reviews(args.url)

    save_dir = os.path.join(os.getcwd(), "review_data")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    result = []
    for review in tqdm.tqdm(reviews.values()):
        place, score, isfull = parse_title(review["title"])
        text, images = crawl_review_article(review["url"])
        
        result.append({"place":place, "score": score, "max_flavor_score": isfull, "review": text, "images": images})
        time.sleep(0.5)

    with open(os.path.join(save_dir, f"{args.title}.json"), "w", encoding="UTF-8-SIG") as fout:
        json.dump(result, fout, ensure_ascii=False)
