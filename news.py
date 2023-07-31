from bs4 import BeautifulSoup
import urllib.request,sys,time
from bs4 import BeautifulSoup
import requests
import pandas as pd
import openai
openai.api_key = "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"
model_engine = "text-davinci-003"
url="https://www.moneycontrol.com/news/business/economy/"
page=requests.get(url)
print(page.status_code)

# print(page.text)
soup = BeautifulSoup(page.text, "html.parser")
links=soup.find_all('li',attrs={'class':'clearfix'})
for i in links:
    text=i.find('p').text
    if "SBI" in text:
        n=text
        prompt1="Give me the news sentiment Analysis related to stocks price by giving a score between 0-10: Also give me the stock names that will be affected by this news. Also give me some your analysis in text as well as in score: The news is as follows : %s "%(n)
        print(n)
    # print(type(text))
completion1 = openai.Completion.create(
    engine=model_engine,
    prompt=prompt1,
    max_tokens=1024,
    n=1,
    stop=None,
    temperature=0.5,
)
# print(prompt1)
analysis = completion1.choices[0].text
print(analysis)