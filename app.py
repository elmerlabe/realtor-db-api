from asyncio import constants
import csv
from functools import wraps
import jwt
from datetime import datetime
from email.policy import default
from numbers import Real
from urllib import request
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS 

app = Flask(__name__)
app.secret_key = "1234"
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:root@localhost:5432/realtor-db'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
CORS(app)
db = SQLAlchemy(app)



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(50))
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.now())


class Realtor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50))
    full_name = db.Column(db.String(50))
    first_name = db.Column(db.String(50))
    middle_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    suffix = db.Column(db.String(10))
    office_name = db.Column(db.String(200))
    office_address_1 = db.Column(db.String(200))
    office_address_2 = db.Column(db.String(200))
    office_city = db.Column(db.String(100))
    office_state = db.Column(db.String(10))
    office_zip = db.Column(db.String(10))
    office_country = db.Column(db.String(50))
    office_phone = db.Column(db.String(50))
    office_fax = db.Column(db.String(50))
    cellphone = db.Column(db.String(50))
    remarks = db.Column(db.String(100))
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.now())

    def __repr__(self):
        return '<Realtor %r>' % self.email




def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        d = request.get_json()
        token = d.get('token')
        #print(d)

        if not token:
            return {"message": "a valid token is missing"}
        try:
            data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
            cUser = User.query.get(data['id'])
        except:
            return {'message': 'token is invalid'}

        return f(cUser, *args, **kwargs)         
    return decorator   


@app.route("/")
def index():
    return {"result":True, "message": "API is online"}


@app.route("/signin", methods=['POST'])
def signin():
    d = request.get_json()
    print(d)
    username = d['username']
    password = d['password']

    user = User.query.filter_by(username=username).first()
    if user:
        if check_password_hash(user.password, password):
            token = jwt.encode({'id':user.id}, app.secret_key, "HS256")
            return {"result":True,"token":token}
        else:
            return {"result": False, "message": "Invalid password"}
    else:
        return {"result": False, "message": "Invalid username"}

@app.route("/getUserFromToken", methods=['POST'])
@token_required
def getUserFromToken(cUser):
    return {"result": True, "user":cUser.username}


@app.route("/getAgentFromId", methods=['POST'])
@token_required
def getAgentFromId(cUser):
    d = request.get_json()
    id = d.get('id')
    r = Realtor.query.get(id)

    obj = []
    obj.insert(0, {"_id": r.id, "email": r.email, "full_name": r.full_name, "first_name": r.first_name, "middle_name": r.middle_name, "last_name": r.last_name,
                    "suffix": r.suffix, "office_name": r.office_name, "office_address_1": r.office_address_1, "office_address_2": r.office_address_2,
                    "office_city": r.office_city, "office_state": r.office_state, "office_zip": r.office_zip, "office_country": r.office_country,
                    "office_phone": r.office_phone, "office_fax": r.office_fax, "cellphone": r.cellphone, "remarks": r.remarks, "date_created":r.date_created})

    return {"result": True, "data": obj}


@app.route("/updateAgentInfo", methods=['PUT'])
@token_required
def updateAgentInfo(cUser):
    d = request.get_json()
    data = d.get('data')
    id = d.get('id')

    r = Realtor.query.get(id)

    r.email = data[0]['value']
    r.full_name = data[1]['value']
    r.first_name = data[2]['value']
    r.middle_name = data[3]['value']
    r.last_name = data[4]['value']
    r.suffix = data[5]['value']
    r.office_name = data[6]['value']
    r.office_address_1 = data[7]['value']
    r.office_address_2 = data[8]['value']
    r.office_city = data[9]['value']
    r.office_state = data[10]['value']
    r.office_zip = data[11]['value']
    r.office_country = data[12]['value']
    r.office_phone = data[13]['value']
    r.office_fax = data[14]['value']
    r.cellphone = data[15]['value']
    db.session.commit()


    return {"result": True, "message": "Successfully Updated!"}



@app.route("/getRealtors", methods=['POST', 'GET'])
@token_required
def getRealtors(cUser):
    page = request.args.get("page", type=int)
    per_page = request.args.get("per_page", type=int)
    
    realtors = Realtor.query.paginate(page=page, per_page=per_page)

    print(per_page)

    obj = []
    cnt = 0

    realtors.items.sort(key=lambda x: x.full_name, reverse=True)

    for r in realtors.items:

        obj.insert(cnt, {"_id": r.id, "email": r.email, "full_name": r.full_name, "first_name": r.first_name, "middle_name": r.middle_name, "last_name": r.last_name,
                        "suffix": r.suffix, "office_name": r.office_name, "office_address_1": r.office_address_1, "office_address_2": r.office_address_2,
                        "office_city": r.office_city, "office_state": r.office_state, "office_zip": r.office_zip, "office_country": r.office_country,
                        "office_phone": r.office_phone, "office_fax": r.office_fax, "cellphone": r.cellphone, "remarks": r.remarks, "date_created":r.date_created})
    

    return {"realtors":obj, "page":page, "pages":realtors.pages, "next_page":realtors.next_num, "prev_page": realtors.prev_num, "total": realtors.total}




#Insert mockdata to database 
'''with open("MOCKDATA/NationalRealtorFilePart1.csv", "r") as csv_file:
    csv_reader = csv.DictReader(csv_file, delimiter=',')
    cnt = 0

    for c in csv_reader:
        if cnt < 5000:
            cnt +=1
            print(cnt)
            realtor = Realtor(email=c['Email'], full_name=c['Full Name'], first_name=c['First Name'], middle_name=c['Middle Name'], last_name=c['Last Name'], 
                              suffix=c['Suffix'], office_name=c['Office Name'], office_address_1=c['Office Address1'], office_address_2=c['Office Address2'],
                              office_city=c['Office City'], office_state=c['Office State'], office_zip=c['Office Zip'], office_country=c['Office County'],
                              office_phone=c['Office Phone'], office_fax=c['Office Fax'], cellphone=c['Cell Phone'], remarks="", date_created=datetime.now())

            db.session.add(realtor)
            db.session.commit()
        else:
            break

    print("Total realtors added: ")
    print(cnt)'''


if __name__ == '__main__':
    app.run(debug=True, port=6001)