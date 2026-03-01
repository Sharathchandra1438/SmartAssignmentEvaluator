from pymongo import MongoClient

client = MongoClient(
"mongodb+srv://sharathchandra7060:Sharath123@clustertest.v1shdwx.mongodb.net/assignmentDB?retryWrites=true&w=majority"
)

db = client["assignmentDB"]

users=db["users"]

#################################################
# LOAD USERS
#################################################

def load_users():

    data=[]

    for u in users.find():

        data.append({

            "name":u.get("name",""),
            "email":u.get("email",""),
            "password":u.get("password",""),
            "role":u.get("role","")

        })

    return data


#################################################
# SAVE USERS
#################################################

def save_users(data):

    users.insert_one(data)