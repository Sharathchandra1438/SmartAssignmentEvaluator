from fastapi import FastAPI, UploadFile, File, Form, Request
from pymongo import MongoClient
from pdf2image import convert_from_bytes
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from bson import ObjectId
import pytesseract
import torch
import torchvision.transforms as transforms
from torchvision import models
import torch.nn as nn
from collections import Counter
import json
import os
from rapidfuzz import fuzz

##################################################
# FASTAPI
##################################################

app = FastAPI()

##################################################
# PATH SETTINGS
##################################################

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

templates = Jinja2Templates(
    directory=os.path.join(BASE_DIR, "templates")
)

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static"
)

##################################################
# CORS
##################################################

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

##################################################
# WEBSITE ROUTES
##################################################

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {"request": request}
    )


@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )


@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {"request": request}
    )


@app.get("/student")
def student_page(request: Request):
    return templates.TemplateResponse(
        "student.html",
        {"request": request}
    )


@app.get("/teacher")
def teacher_page(request: Request):
    return templates.TemplateResponse(
        "teacher.html",
        {"request": request}
    )

@app.get("/navbar")
def navbar(request: Request):
    return templates.TemplateResponse(
        "navbar.html",
        {"request": request}
    )

##################################################
# MONGODB
##################################################

client = MongoClient(
"mongodb+srv://sharathchandra7060:Sharath123@clustertest.v1shdwx.mongodb.net/assignmentDB?retryWrites=true&w=majority"
)

db = client["assignmentDB"]

assignments = db["assignments"]
results = db["results"]
users = db["users"]

##################################################
# TESSERACT
##################################################

# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

##################################################
# WRITER MODEL
##################################################

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

with open("classes.json") as f:
    class_names = json.load(f)

model = models.resnet18(weights=None)
model.fc = nn.Linear(model.fc.in_features, len(class_names))

model.load_state_dict(
    torch.load("writer_model.pth", map_location=device)
)

model.to(device)
model.eval()

transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=3),
    transforms.Resize((224,224)),
    transforms.ToTensor(),
    transforms.Normalize([0.5,0.5,0.5],[0.5,0.5,0.5])
])

##################################################
# REGISTER API
##################################################

@app.post("/registerUser")
async def registerUser(

    name:str=Form(...),
    email:str=Form(...),
    password:str=Form(...),
    role:str=Form(...)

):

    existing=users.find_one({"email":email})

    if existing:
        return {"message":"User already exists"}

    users.insert_one({

        "name":name,
        "email":email,
        "password":password,
        "role":role

    })

    return {"message":"Registered Successfully"}


##################################################
# LOGIN API
##################################################

@app.post("/loginUser")
async def loginUser(

    email:str=Form(...),
    password:str=Form(...)

):

    user=users.find_one({

        "email":email,
        "password":password

    })

    if not user:
        return {"message":"Invalid Login"}

    return {

        "name":user["name"],
        "email":user["email"],
        "role":user["role"]

    }


##################################################
# CREATE ASSIGNMENT
##################################################

@app.post("/createAssignment")
async def create_assignment(

    teacherName:str=Form(...),
    teacherEmail:str=Form(...),
    title:str=Form(...),
    points:str=Form(...)

):

    pointList=points.split("\n")

    assignments.insert_one({

        "teacherName":teacherName,
        "teacherEmail":teacherEmail,
        "title":title,
        "points":pointList

    })

    return {"message":"Assignment Created"}


##################################################
# GET ASSIGNMENTS
##################################################

@app.get("/assignments")
def get_assignments():

    data=[]

    for a in assignments.find():

        data.append({

            "id":str(a["_id"]),
            "title":a["title"],
            "teacher":a["teacherName"]

        })

    return data


##################################################
# OCR FUNCTIONS
##################################################

def ocr_image(image):

    image=image.convert("L")

    text=pytesseract.image_to_string(image)

    return text


def extract_text(pages):

    text=""

    for page in pages:
        text+=ocr_image(page)+" "

    return text.lower()


##################################################
# WRITER DETECTION
##################################################

def detect_writer(pages):

    predictions=[]

    for page in pages:

        img=transform(page).unsqueeze(0).to(device)

        with torch.no_grad():

            output=model(img)

            _,predicted=torch.max(output,1)

        predictions.append(
            class_names[predicted.item()]
        )

    writer=Counter(predictions).most_common(1)[0][0]

    total_pages=len(pages)

    return writer,total_pages


##################################################
# SIMILARITY
##################################################

def similarity(points,text):

    matched=0
    total=len(points)

    for p in points:

        score=fuzz.partial_ratio(
            p.lower(),
            text
        )

        if score>50:
            matched+=1

    if total==0:
        return 0,0,0

    finalScore=(matched/total)*100

    return finalScore,matched,total

##################################################
# SUBMIT ASSIGNMENT
##################################################

@app.post("/submitAssignment")
async def submit(

    studentName: str = Form(...),
    rollNo: str = Form(...),
    assignmentId: str = Form(...),
    file: UploadFile = File(...)

):

    pdf = await file.read()

    pages = convert_from_bytes(pdf, dpi=300)

    text = extract_text(pages)

    assignment = assignments.find_one({
        "_id": ObjectId(assignmentId)
    })

    points = assignment["points"]

    score, matched, total = similarity(points, text)

    unanswered = total - matched

    writer, pagesCount = detect_writer(pages)

    result = {

        "studentName": studentName,
        "rollNo": rollNo,

        "writerName": writer,
        "pages": pagesCount,

        "title": assignment["title"],
        "teacher": assignment["teacherName"],
        "teacherEmail": assignment["teacherEmail"],

        "score": round(score,2),

        "totalQuestions": total,
        "matchedQuestions": matched,
        "unansweredQuestions": unanswered

    }

    # Insert into MongoDB
    inserted = results.insert_one(result)

    # Convert ObjectId → string
    result["_id"] = str(inserted.inserted_id)

    return result

##################################################
# TEACHER RESULTS
##################################################

@app.get("/results/{teacherEmail}")
def teacher_results(teacherEmail):

    data=[]

    for r in results.find({"teacherEmail":teacherEmail}):

        data.append({

            "student":r["studentName"],
            "roll":r["rollNo"],

            "writer":r["writerName"],
            "pages":r["pages"],

            "title":r["title"],

            "score":r["score"],

            "totalQuestions":r["totalQuestions"],
            "matchedQuestions":r["matchedQuestions"]

        })

    return data


##################################################
# ALL RESULTS
##################################################

@app.get("/results")
def all_results():

    data=[]

    for r in results.find():

        data.append({

            "student":r["studentName"],
            "roll":r["rollNo"],

            "writer":r["writerName"],
            "pages":r["pages"],

            "title":r["title"],

            "score":r["score"],

            "totalQuestions":r["totalQuestions"],
            "matchedQuestions":r["matchedQuestions"]

        })

    return data