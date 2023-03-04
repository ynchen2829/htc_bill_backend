import os
import json
import openai
from bs4 import BeautifulSoup
import requests
import pymongo
from pymongo import MongoClient, InsertOne

openai.api_key = os.environ['OPEN_API_KEY']
mongo_clientkey = os.environ['MONGO_HTC_KEY']
def main():
    bill_list = []
    #for bill in bill_list:
    # response = requests.get(bill["source"])
    response = requests.get("https://capitol.texas.gov/tlodocs/873/billtext/html/HB00001I.htm")
    soup = BeautifulSoup(response.content, features= "html.parser")
    text = soup.get_text(strip=True)
    summary_str = "Please summarize the following piece of legislation in at most a paragraph and pretend you are presenting it to a group of middle school students. The legislation is: {}".format(text)
    title_str = "Please create a title for the following piece of legislation. Make the title engaging and no longer than 10 words. The legislation is: {}".format(text)
    keyword_str = "Please produce 5 single word keywords in csv format for the following piece of legislation: {}".format(text)
    
    #get responses from gpt3 based on the prompts
    response_summary = openai.ChatCompletion.create(
    model="gpt-3.5-turbo", 
    messages=[{"role": "user", "content": summary_str }],
    )
    response_title = openai.ChatCompletion.create(
    model="gpt-3.5-turbo", 
    messages=[{"role": "user", "content": title_str }],
    )
    response_keyword = openai.ChatCompletion.create(
    model="gpt-3.5-turbo", 
    messages=[{"role": "user", "content": keyword_str }],
    )
    bill = dict()
    #populate the dictionary for the bill object
    bill["title"] = response_title.get("choices")[0].get("message").get("content")
    bill["description"] = response_summary.get("choices")[0].get("message").get("content")
    bill["keywords"] = [x.strip() for x in response_keyword.get("choices")[0].get("message").get("content").split(',')]

    mongo_str = "mongodb+srv://ynchen2829:"+mongo_clientkey+"@htc-data-cluster0.tmj9bij.mongodb.net/?retryWrites=true&w=majority"
    print(mongo_str)
    client = pymongo.MongoClient(mongo_str)
    db = client['htc_bill']
    collection = db['full']
    collection.insert_one(bill)

if __name__ == "__main__":
    main()