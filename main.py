import uvicorn
import firebase_admin
import pyrebase
import json 
import pandas as pd
import numpy as np
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
import chainer
import chainer.functions as F
import chainer.links as L
data_reliance = pd.read_csv('static/assets/data/reliance.csv')
data_tata = pd.read_csv('static/assets/data/tatamotors.csv')
# data['Date'] = pd.to_datetime(data['Date'])
# data = data.set_index('Date')
data_reliance=data_reliance.dropna()
data_tata=data_tata.dropna()

#-------------------------------Login--------------------------------------------------------------------------

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

#------------------------------Setting Gym Environment---------------------------------------------------------------------------------
class Environment1:    
    def __init__(self, data, history_t=85):
        self.data = data
        self.history_t = history_t
        self.reset()
        
    def reset(self):
        self.t = 0
        self.done = False
        self.profits = 0
        self.positions = []
        self.position_value = 0
        self.history = [0 for _ in range(self.history_t)]
        return [self.position_value] + self.history # obs
    
    def step(self, act):
        reward = 0
        
        # act = 0: stay, 1: buy, 2: sell
        if act == 1:
            self.positions.append(self.data.iloc[self.t, :]['Close'])
        elif act == 2: # sell
            if len(self.positions) == 0:
                reward = -1
            else:
                profits = 0
                for p in self.positions:
                    profits += (self.data.iloc[self.t, :]['Close'] - p)
                reward += profits
                self.profits += profits
                self.positions = []
        
        # set next time
        self.t += 1
        self.position_value = 0
        for p in self.positions:
            self.position_value += (self.data.iloc[self.t, :]['Close'] - p)
        self.history.pop(0)
        self.history.append(self.data.iloc[self.t, :]['Close'] - self.data.iloc[(self.t-1), :]['Close'])
        
        # clipping reward
        if reward > 0:
            reward = 1
        elif reward < 0:
            reward = -1
        
        return [self.position_value] + self.history, reward, self.done # obs, reward, done





#---------------------------------Initialising the DQN model Classes--------------------------------------------------------------------------------------
class DQNQ_Network(chainer.Chain):

        def __init__(self, input_size, hidden_size, output_size):
            super(DQNQ_Network, self).__init__(
                fc1 = L.Linear(input_size, hidden_size),
                fc2 = L.Linear(hidden_size, hidden_size),
                fc3 = L.Linear(hidden_size, output_size)
            )

        def __call__(self, x):
            h = F.relu(self.fc1(x))
            h = F.relu(self.fc2(h))
            y = self.fc3(h)
            return y

        def reset(self):
            self.zerograds()





#---------------------------------Initialising the DDQN model Classes----------------------------------------------------------------------------------------- 
class DDQNQ_Network(chainer.Chain):

        def __init__(self, input_size, hidden_size, output_size):
            super(DDQNQ_Network, self).__init__(
                fc1 = L.Linear(input_size, hidden_size),
                fc2 = L.Linear(hidden_size, hidden_size),
                fc3 = L.Linear(hidden_size, output_size)
            )

        def __call__(self, x):
            h = F.relu(self.fc1(x))
            h = F.relu(self.fc2(h))
            y = self.fc3(h)
            return y

        def reset(self):
            self.zerograds()




#-------------------------------------------Initialising the DuelDQN model Classes-------------------------------------------------------------------------------------
class DuelDQNQ_Network(chainer.Chain):

        def __init__(self, input_size, hidden_size, output_size):
            super(DuelDQNQ_Network, self).__init__(
                fc1 = L.Linear(input_size, hidden_size),
                fc2 = L.Linear(hidden_size, hidden_size),
                fc3 = L.Linear(hidden_size, hidden_size//2),
                fc4 = L.Linear(hidden_size, hidden_size//2),
                state_value = L.Linear(hidden_size//2, 1),
                advantage_value = L.Linear(hidden_size//2, output_size)
            )
            self.input_size = input_size
            self.hidden_size = hidden_size
            self.output_size = output_size

        def __call__(self, x):
            h = F.relu(self.fc1(x))
            h = F.relu(self.fc2(h))
            hs = F.relu(self.fc3(h))
            ha = F.relu(self.fc4(h))
            state_value = self.state_value(hs)
            advantage_value = self.advantage_value(ha)
            advantage_mean = (F.sum(advantage_value, axis=1)/float(self.output_size)).reshape(-1, 1)
            q_value = F.concat([state_value for _ in range(self.output_size)], axis=1) + (advantage_value - F.concat([advantage_mean for _ in range(self.output_size)], axis=1))
            return q_value

        def reset(self):
            self.zerograds()



#------------------------------------------Function for extracting live stock data from Website---------------------------------------------------------------------------------
def extract_data(url):
    headers = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"}
    response = requests.get(url,headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table',{"class":"W(100%) M(0)"})
    data = []
    for row in table.find_all('tr'):
        row_data = []
        for cell in row.find_all('td'):
            row_data.append(cell.text)
        data.append(row_data)

    df = pd.DataFrame(data)
    df=df.dropna()
    close1=list(df.iloc[1:87,4])
    close2=list(df.iloc[2:88,4])
    close1.reverse()
    close2.reverse()
    for i in range(len(close1)):
        n=close1[i]
        if("," in n):
            s=n.replace(",","")
        else:
            s=n    
        num=float(s)
        close1[i]=num

    for i in range(len(close2)):
        n=close2[i]
        if("," in n):
            s=n.replace(",","")
        else:
            s=n    
        num=float(s)
        close2[i]=num

    state=np.array(close2)-np.array(close1)
    return state            


#----------------------------------------------------Prediction----------------------------------------------------------------------------
def reliance_prediction(state):
    from chainer import serializers
    # Load the model
    model = DuelDQNQ_Network(input_size=86, hidden_size=100, output_size=3)  # Create an instance of your model
    serializers.load_npz('static/assets/models/reliance_dueldqn.npz', model)
    act=model.__call__(np.array(state, dtype=np.float32).reshape(1, -1))
    arr=act.array
    argmax_index = np.argmax(arr)
    if(argmax_index==0):
        return "HOLD"
    elif(argmax_index==1):
        return "BUY"
    else:
        return "SELL"

    
#-----------------------------------------------------------------------------------------------------------------------

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
    Values.remove(Values[3])
    data={}
    for i in range(len(Ratios)):
        ratio=Ratios[i].get_text()
        print(ratio)
        ratio=ratio.strip()
        ratio=ratio.replace(" ","")
        ratio=ratio.replace("/","")
        value=Values[i].get_text()
        value=value.replace(',','')
        value=float(value)
        data[ratio]=value
    data["request"]=request
    # print(data)
    # print(Values)    
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
    Values.remove(Values[3])
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
    url='https://finance.yahoo.com/quote/RELIANCE.NS/history?p=RELIANCE.NS'
    state=extract_data(url)
    action=reliance_prediction(state)
    url1="https://www.screener.in/company/RELIANCE/consolidated/"
    page=requests.get(url1)
    print(page.status_code)
    # print(page.text)
    soup = BeautifulSoup(page.text, "html.parser")
    links=soup.find_all('li',attrs={'class':'flex flex-space-between'})
    Ratios=soup.find_all('span',attrs={'class':'name'})
    Values=soup.find_all('span',attrs={'class':'number'})
    Values.remove(Values[3])
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
    data["reliance_action"]=action
    if(action=="BUY"):
        text="According to our AI Model the best action you can take is to BUY more stocks of Reliance for future gains.<br>If You have not purchased the stock till now this is the best time to invest in this. You can buy it now for great gains in the future.  Please see our other analysis such as statistical analysis as well as news review to make up your mind. Do not follow our advice blindly"
        data["text"]=text
    elif(action=="SELL"):
        text="According to our AI Model the best action you can take is to Sell stocks of Reliance for gains.You can sell it now according to our ML model. Please see our other analysis such as statistical analysis as well as news review to make up your mind. Do not follow our advice blindly"
        data["text"]=text
    else:
        text="According to our AI Model the best action you can take is to HOLD stocks of Reliance for future gains.If You have not purchased the stock till now this is the time to invest in this.You can buy it now for great gains in the future if you do not own these stocks. Please see our other analysis such as statistical analysis as well as news review to make up your mind. Do not follow our advice blindly"
        data["text"]=text    

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
       
       return  templates.TemplateResponse("index.html", context={"request": request,"action":"Hold"})
       
        
               
   except:
       alert1=1
       return  templates.TemplateResponse("pages-login.html", context={"request": request,"alert1":str(alert1)})
 
# ping endpoint
 
if __name__ == "__main__":
   app.run() 
#    uvicorn.run("main:app")