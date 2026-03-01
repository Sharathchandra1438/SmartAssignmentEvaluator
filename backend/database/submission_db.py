from pymongo import MongoClient

client = MongoClient(
"mongodb+srv://sharathchandra7060:Sharath123@clustertest.v1shdwx.mongodb.net/assignmentDB?retryWrites=true&w=majority"
)

db = client["assignmentDB"]

results=db["results"]

#################################################
# LOAD SUBMISSIONS
#################################################

def load_submissions():

    data=[]

    for r in results.find():

        data.append({

            "student":r.get("studentName",""),
            "roll":r.get("rollNo",""),

            "title":r.get("title",""),

            "score":r.get("score",0),

            "teacherEmail":r.get("teacherEmail","")

        })

    return data


#################################################
# SAVE SUBMISSION
#################################################

def save_submissions(data):

    results.insert_one(data)