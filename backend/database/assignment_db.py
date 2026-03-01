from pymongo import MongoClient
from bson import ObjectId

client = MongoClient(
"mongodb+srv://sharathchandra7060:Sharath123@clustertest.v1shdwx.mongodb.net/assignmentDB?retryWrites=true&w=majority"
)

db = client["assignmentDB"]

assignments = db["assignments"]


#################################################
# LOAD ASSIGNMENTS
#################################################

def load_assignments():

    data=[]

    for a in assignments.find():

        data.append({

            "id":str(a["_id"]),
            "title":a.get("title",""),
            "questions":"\n".join(a.get("points",[])),
            "keywords":"",

            "teacherEmail":a.get("teacherEmail","")

        })

    return data


#################################################
# SAVE ASSIGNMENT (OPTIONAL)
#################################################

def save_assignments(data):

    assignments.insert_one(data)