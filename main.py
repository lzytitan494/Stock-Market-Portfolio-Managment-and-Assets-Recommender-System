import uvicorn
import firebase_admin
import pyrebase
import json 
from firebase_admin import credentials, auth
from fastapi import FastAPI, Request,Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from bs4 import BeautifulSoup
import urllib.request,sys,time
from bs4 import BeautifulSoup
import requests

cred = credentials.Certificate('stock-market-portfolio-76be4-firebase-adminsdk-ds64q-194b25fe3e.json')
if not firebase_admin._apps:
    firebase = firebase_admin.initialize_app(cred)
pb = pyrebase.initialize_app(json.load(open('firebase_config.json')))
app = FastAPI()
app.mount("/static", StaticFiles(directory="static/"), name="static")
templates = Jinja2Templates(directory="templates/")
allow_all = ['*']
app.add_middleware(
   CORSMiddleware,
   allow_origins=allow_all,
   allow_credentials=True,
   allow_methods=allow_all,
   allow_headers=allow_all
)
 
# signup endpoint
@app.get("/pages-register.html", include_in_schema=False)
async def viewpage(request:Request):
    return templates.TemplateResponse("pages-register.html", context={"request": request})

@app.get("/", include_in_schema=False)
async def viewpage(request:Request):
    return templates.TemplateResponse("home.html", context={"request": request})

@app.get("/pages-login.html", include_in_schema=False)
async def viewpage(request:Request):
    return templates.TemplateResponse("pages-login.html", context={"request": request})

@app.get("/index.html", include_in_schema=False)
async def viewpage(request:Request):
    return templates.TemplateResponse("index.html", context={"request": request})

@app.get("/users-profile.html", include_in_schema=False)
async def viewpage(request:Request):
    return templates.TemplateResponse("users-profile.html", context={"request": request})

@app.post("/pages-register.html", include_in_schema=False)
async def login(request:Request,email: str = Form(), password: str = Form(),name: str= Form(),mobile: str=Form()):
   print(email)
   print(password)
   print(name)
   print(mobile)
   try:
       user = auth.create_user(
           email=email,
           password=password,
           display_name=name,
           phone_number=mobile
       )
       alert2=1
       return  templates.TemplateResponse("pages-register.html", context={"request": request,"alert2":str(alert2)})   
   except:
       alert3=1
       return  templates.TemplateResponse("pages-register.html", context={"request": request,"alert2":str(alert3)})

#For Tata Motors

@app.get("/analysis_tata.html", include_in_schema=False)
async def viewpage(request:Request):
    url1="https://www.screener.in/company/TATAMOTORS/consolidated/"
    page=requests.get(url1)
    print(page.status_code)
    # print(page.text)
    soup = BeautifulSoup(page.text, "html.parser")
    links=soup.find_all('li',attrs={'class':'flex flex-space-between'})
    Ratios=soup.find_all('span',attrs={'class':'name'})
    Values=soup.find_all('span',attrs={'class':'number'})
    data={}
    for i in range(len(Ratios)):
        ratio=Ratios[i].get_text()
        ratio=ratio.strip()
        ratio=ratio.replace(" ","")
        ratio=ratio.replace("/","")
        value=Values[i].get_text()
        value=value.replace(',','')
        value=float(value)
        data[ratio]=value
    data["request"]=request
    print(data)    
    return templates.TemplateResponse("analysis_tata.html", context=data)   


@app.get("/analysis_ntpc.html", include_in_schema=False)
async def viewpage(request:Request):
    url1="https://www.screener.in/company/NTPC/consolidated/"
    page=requests.get(url1)
    print(page.status_code)
    # print(page.text)
    soup = BeautifulSoup(page.text, "html.parser")
    links=soup.find_all('li',attrs={'class':'flex flex-space-between'})
    Ratios=soup.find_all('span',attrs={'class':'name'})
    Values=soup.find_all('span',attrs={'class':'number'})
    data={}
    for i in range(len(Ratios)):
        ratio=Ratios[i].get_text()
        ratio=ratio.strip()
        ratio=ratio.replace(" ","")
        ratio=ratio.replace("/","")
        value=Values[i].get_text()
        value=value.replace(',','')
        value=float(value)
        data[ratio]=value
    data["request"]=request
    print(data)    
    return templates.TemplateResponse("analysis_ntpc.html", context=data)


@app.get("/analysis_reliance.html", include_in_schema=False)
async def viewpage(request:Request):
    url1="https://www.screener.in/company/RELIANCE/consolidated/"
    page=requests.get(url1)
    print(page.status_code)
    # print(page.text)
    soup = BeautifulSoup(page.text, "html.parser")
    links=soup.find_all('li',attrs={'class':'flex flex-space-between'})
    Ratios=soup.find_all('span',attrs={'class':'name'})
    Values=soup.find_all('span',attrs={'class':'number'})
    data={}
    for i in range(len(Ratios)):
        ratio=Ratios[i].get_text()
        ratio=ratio.strip()
        ratio=ratio.replace(" ","")
        ratio=ratio.replace("/","")
        value=Values[i].get_text()
        value=value.replace(',','')
        value=float(value)
        data[ratio]=value
    data["request"]=request
    print(data)    
    return templates.TemplateResponse("analysis_reliance.html", context=data)



# async def signup(request: Request):
   
#    req = await request.json()
#    email = req['email']
#    password = req['password']
#    if email is None or password is None:
#        return HTTPException(detail={'message': 'Error! Missing Email or Password'}, status_code=400)
#    try:
#        user = auth.create_user(
#            email=email,
#            password=password
#        )
#        return JSONResponse(content={'message': f'Successfully created user {user.uid}'}, status_code=200)    
#    except:
#        return HTTPException(detail={'message': 'Error Creating User'}, status_code=400)
 
# login endpoint
@app.post("/pages-login.html", include_in_schema=False)
async def login(request:Request,email1: str = Form(), password1: str = Form()):
   print(email1)
   print(password1)
   try:
       user = auth.get_user_by_email(email1)
    #    print(user)
    #    pas="Yash@1234"
    #    pas=user.password
    #    print(pas)
       login = pb.auth().sign_in_with_email_and_password(email1, password1)
       print(user)
       
       return  templates.TemplateResponse("index.html", context={"request": request})
       
        
               
   except:
       alert1=1
       return  templates.TemplateResponse("pages-login.html", context={"request": request,"alert1":str(alert1)})
 
# ping endpoint
 
if __name__ == "__main__":
   app.run() 
#    uvicorn.run("main:app")