import requests
from bs4 import BeautifulSoup
from datetime import datetime
import openai
import json
import pymongo
from pymongo import MongoClient, InsertOne

import os
import sys
import time

mongo_clientkey = os.environ["MONGO_HTC_KEY"]

def makeBill(history_url, base_string):
    time.sleep(1)
    retries = 1
    success = False
    while not success:
        try:
            history_page = requests.get(history_url, timeout = 5)
            success = True
        except requests.exceptions.RequestException as e:
            wait = retries*5
            print("Error! Waiting %s secs and re-trying..." % wait)
            sys.stdout.flush()
            time.sleep(wait)
            retries += 1

    history_soup = BeautifulSoup(history_page.content, "html.parser")
    bill_name = history_soup.find("span", id = "usrBillInfoTabs_lblBill").text
    print(f"Processing Bill: {bill_name}")
    bill_author = history_soup.find("td", id = "cellAuthors").text

    bill_session = history_soup.find("span", id = "usrBillInfoTabs_lblItem1Data").text

    date_string = history_soup.find("td", id = "cellLastAction").text.split()[0]
    bill_last_action = datetime.strptime(date_string, "%m/%d/%Y").isoformat()

    try:
      date_filed_string = history_soup.find("td", text = "\xa0Filed\xa0").find_next_sibling().find_next_sibling().get_text(strip=True)
      bill_date_filed = datetime.strptime(date_filed_string, "%m/%d/%Y").isoformat()
    except:
      date_filed_string = history_soup.find("td", text = "\xa0Received by the Secretary of the Senate\xa0").find_next_sibling().find_next_sibling().get_text(strip=True)
      bill_date_filed = datetime.strptime(date_filed_string, "%m/%d/%Y").isoformat()

    table = history_soup.find("td", id = "cellSubjects")
    raw_subjects = table.text.split(")")
    bill_subjects = [x[-5:] for x in raw_subjects[:-1]]
    bill_tags = []

    enviro = ["S0431", "S8821", "S0330", "S2791", "S6058", "S0591", "SL9IT", "S0750", "I0067", "S0561", "S0067", "S0536", "S0572", "S0068", "SI3J9", "S8878", "I0314", "I0317", "I0319", "I0315", "IP9BV", "I0318", "I0316", "IA9YE", "I0325", "I0340", "I0333", "I0335", "I0336", "I0330", "I0320", "S0284", "S0691", "S0390", "S0222", "S0295", "S0654", "I0536", "I0545", "S0287", "I0585", "I0560", "I0565", "I0555", "I0570", "S1080", "S0611", "S0503", "I0013", "I0760", "I0810", "I0809", "S6061", "I0823", "S0719"]
    gender_sex = ["S3940", "S2255", "I0005", "S0328", "S9797", "S0683", "I0171", "S0466", "I0352", "I0350", "S3343", "S0767", "S0055", "S0268", "S0360", "S6017", "S0180", "S0382", "S0031", "S0200", "S0379", "S0294", "S0344", "S0440", "S0827", "S9791", "S4375", "S4376", "S0160", "S0099", "S0085", "S2194", "S0044"]
    transport = ["I0390", "S0753", "I0822", "I0823", "I0824", "I0821", "I0820", "S0220"]
    taxation = ["I0812", "I0808", "I0775", "I0780", "I0810", "I0807", "I0815", "I0806", "I0805", "I0811", "I0809", "I0813", "I0796", "I0792", "I0798", "I0793", "I0797", "I0791", "I0794", "I0800", "I0785", "I0790"]
    labor = ["S0078", "I0480", "I0500", "I0490", "I0465", "I0475", "I0485", "I0470", "I0495", "I0496"]
    housing = ["I0403", "I0407", "I0405", "I0404", "I0408", "I0406", "I0409"]
    health = ["S0115", "I0387", "S0248", "S0706", "S0562", "S0853", "I0382", "I0388", "I0384", "I0385", "I0386", "I0383", "I0389", "I0381"]
    elections = ["S0018", "I0277", "I0290", "I0280", "I0260", "I0305", "I0310", "I0300", "I0308", "I0275", "I0295", "I0285", "I0265", "I0283", "I0270"]
    education = ["S0178", "S0610", "S0392", "S0134", "I0213", "I0215", "I0219", "I0255", "I0257", "S0142", "I0256", "S0257", "I0236", "I0232", "I0231", "I0237", "I0223", "I0238", "I0224", "I0234", "I0235", "I0258", "I0233", "I0225", "I0222", "I0007", "I0227", "I0245", "S0232", "I0228", "I0244", "I0247", "I0241", "I0250", "I0230", "I0248", "I0246", "I0239", "S0131", "I0243", "I0242", "I0229", "I0226", "S3383", "I0240", "I0249", "S0118", "I0221", "I0220", "S0465", "S0423"]
    guns = ["S0241", "S0427", "S0184", "I0887"]
    inclusivity = ["I0032", "S0347", "S0617", "S0124", "S0566", "S397Q", "S4389", "I0201", "S0052", "I0380", "S0088", "S9807", "I0237", "S0465", "S0423", "S0354", "S0444", "S0064", "S0055", "S0076", "I0403", "I0404", "I0409", "S0674", "S0673", "I0530", "I0019", "S0019", "S0441", "S0195", "S0474", "I0646", "S0440", "S0456", "S1174", ]

    if(any(item in bill_subjects for item in enviro)):
        bill_tags.append("Environment")
    if(any(item in bill_subjects for item in gender_sex)):
        bill_tags.append("Gender/Sexuality")
    if(any(item in bill_subjects for item in transport)):
        bill_tags.append("Transportation")
    if(any(item in bill_subjects for item in taxation)):
        bill_tags.append("Taxation")
    if(any(item in bill_subjects for item in labor)):
        bill_tags.append("Labor")
    if(any(item in bill_subjects for item in housing)):
        bill_tags.append("Housing")
    if(any(item in bill_subjects for item in health)):
        bill_tags.append("Health")
    if(any(item in bill_subjects for item in elections)):
        bill_tags.append("Elections")
    if(any(item in bill_subjects for item in education)):
        bill_tags.append("Education")
    if(any(item in bill_subjects for item in guns)):
        bill_tags.append("Guns")
    if(any(item in bill_subjects for item in inclusivity)):
        bill_tags.append("Inclusivity/Accessibility")
  
    text_url = history_url.replace("History", "Text")
    text_page = requests.get(text_url)
    text_soup = BeautifulSoup(text_page.content, "html.parser")

    bill_source = base_string + text_soup.find("img", alt = "HTML").parent.get("href")

    stage_url = history_url.replace("History", "BillStages")
    stage_page = requests.get(stage_url)
    stage_soup = BeautifulSoup(stage_page.content, "html.parser")

    completed_list = stage_soup.find_all("div", class_ = "bill-status-box-complete")
    bill_stage = len(completed_list)
    if(bill_stage == 7):
        bill_status = 2
    elif(stage_soup.find("img", src = "../Images/fail.gif") or stage_soup.find("div", class_="bill-status-box-failed")):
        bill_status = 0
    else:
        bill_status = 1
    bill = {"name": bill_name, "source": bill_source,  "author": bill_author, "state": "TX", "session": bill_session, "timestamp": bill_date_filed, "time_recent": bill_last_action, "status": bill_status, "stage": bill_stage, "tags": bill_tags}
    return bill

def makeBillsList(url, base_string, num):
    page = requests.get(url)

    soup = BeautifulSoup(page.content, "html.parser")
    hyper_links = soup.find_all("a")

    links = [x.get("href") for x in hyper_links]
    #num_links = []
    # for x in num:
    #    num_links.append(links[x])
    num_links = links[0:num] 
    bills = [makeBill(history_url, base_string) for history_url in num_links]

    return bills

def makeFullBillsList(base_string, type, num):
    url = f"https://capitol.texas.gov/Reports/Report.aspx?LegSess=88R&ID={type}filed"
    return makeBillsList(url, base_string, num)

def finalBillList():
    base_string = "https://capitol.texas.gov"
    house_bills = makeFullBillsList(base_string, "house", 30)
    senate_bills = makeFullBillsList(base_string, "senate", 30)

    bill_list = house_bills + senate_bills

    return bill_list

def final():
    bill_list = finalBillList()
    #print(bill_list)

    #data_file = open("data.txt", "r")
    #data = data_file.read()
    #bill_list = json.loads(data)
    # print(len(data))
    mongo_str = "mongodb+srv://ynchen2829:"+mongo_clientkey+"@htc-data-cluster0.tmj9bij.mongodb.net/?retryWrites=true&w=majority"
    print(mongo_str)
    client = pymongo.MongoClient(mongo_str)
    db = client["htc_bill"]
    collection = db["full"]

    for i, bill in enumerate(bill_list):
        if i % 2 == 0:
            time.sleep(65)
        response = requests.get(bill["source"])
        soup = BeautifulSoup(response.content, features= "html.parser")
        text = " ".join(soup.get_text(strip=True).split()[:2000])

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
        #populate the dictionary for the bill object
        bill["title"] = response_title.get("choices")[0].get("message").get("content")
        bill["description"] = response_summary.get("choices")[0].get("message").get("content")
        bill["keywords"] = [x.strip() for x in response_keyword.get("choices")[0].get("message").get("content").split(",")]
        print(bill)
        collection.insert_one(bill)

if __name__ == "__main__":
    final()
