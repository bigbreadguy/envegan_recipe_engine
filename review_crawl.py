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
        "https://developers.whatismybrowser.com/useragents/parse/1240908webkit-based-browser-ios-iphone-webkit",
        "https://developers.whatismybrowser.com/useragents/parse/1261120webkit-based-browser-ios-ipad-webkit",
        "https://developers.whatismybrowser.com/useragents/parse/819115safari-ios-iphone-webkit",
        "https://developers.whatismybrowser.com/useragents/parse/22389882safari-ios-iphone-webkit",
        "https://developers.whatismybrowser.com/useragents/parse/89890032safari-ios-iphone-webkit",
        "https://developers.whatismybrowser.com/useragents/parse/61890android-browser-android-webkit",
        "https://developers.whatismybrowser.com/useragents/parse/88115148chrome-android-blink",
        "https://developers.whatismybrowser.com/useragents/parse/1273795webkit-based-browser-macos-webkit",
        "https://developers.whatismybrowser.com/useragents/parse/61120287safari-macos-webkit",
        "https://developers.whatismybrowser.com/useragents/parse/82436602safari-macos-webkit",
        "https://developers.whatismybrowser.com/useragents/parse/5801373safari-macos-webkit",
        "https://developers.whatismybrowser.com/useragents/parse/133664832chrome-chrome-os-blink",
        "https://developers.whatismybrowser.com/useragents/parse/696837edge-windows-edgehtml",
        "https://developers.whatismybrowser.com/useragents/parse/135322344edge-windows-blink"]

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9", 
        "Accept-Encoding": "gzip, deflate", 
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8", 
        "Dnt": "1", 
        "Host": "httpbin.org", 
        "Upgrade-Insecure-Requests": "1", 
        "User-Agent": user_agents[random.randrange(len(user_agents))], 
    }
    
    response = requests.get(url, headers=headers)

    return response

def crawl_review_article(url:str):
    response = get_response(url)
    soup = BeautifulSoup(response.content, from_encoding="utf-8")

    article = soup.find_all(class_="entry-content")[0]
    paragraphs = article.find_all("p")

    text = ""
    for p in paragraphs:
        t = p.get_text()
        text+=t

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
    soup = BeautifulSoup(response.content, from_encoding="utf-8")

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
    score = splt[1].split(" ")[0][:1]
    
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

    with open(os.path.join(save_dir, f"{args.title}.json", "w", encoding="UTF-8-SIG")) as fout:
        json.dump(result, fout, ensure_ascii=False)
