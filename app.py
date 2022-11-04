from asyncio import constants
import csv
from lib2to3.pgen2 import token
from operator import or_
import re
import flask
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
from sqlalchemy import or_

app = Flask(__name__)
app.secret_key = "1234"
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://mzrnhsngpzhail:8fff0c777d10daa3dea6ec53594028daaf11fa66c82bb85a8b429035d74d1eaa@ec2-3-219-19-205.compute-1.amazonaws.com:5432/d2065pa7oj1vo7' # heroku-postgres
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:root@localhost:5432/realtors-db' # local database
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://everreach_staging:zytjiv-peprib-fyvvU5@everreach.nell.sh/realtors-db" # Nell remote server
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db' # SQLite
CORS(app)
db = SQLAlchemy(app)


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(50))
    createdAt = db.Column(db.DateTime, nullable=False, default=datetime.now())
    updatedAt = db.Column(db.DateTime, nullable=False, default=datetime.now())


class Agents(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255))
    firstName = db.Column(db.String(255))
    middleName = db.Column(db.String(255))
    lastName = db.Column(db.String(255))
    suffix = db.Column(db.String(255))
    officeName = db.Column(db.String(255))
    officeAddress1 = db.Column(db.String(255))
    officeAddress2 = db.Column(db.String(255))
    officeCity = db.Column(db.String(255))
    officeState = db.Column(db.String(255))
    officeZip = db.Column(db.String(255))
    officeCountry = db.Column(db.String(255))
    officePhone = db.Column(db.String(255))
    officeFax = db.Column(db.String(255))
    cellPhone = db.Column(db.String(255))
    createdAt = db.Column(db.DateTime, nullable=False, default=datetime.now())
    updatedAt = db.Column(db.DateTime, nullable=False, default=datetime.now())

    def __repr__(self):
        return '<Agents %r>' % self.email


class Cities(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    stateId = db.Column(db.Integer, db.ForeignKey('states.id'))
    state = db.relationship('States', backref=db.backref('state', lazy=True))
    createdAt = db.Column(db.DateTime, nullable=False, default=datetime.now())
    updatedAt = db.Column(db.DateTime, nullable=False, default=datetime.now())

    def __repr__(self):
        return '<Cities %r>' % self.name


class States(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    longName = db.Column(db.String(255))
    createdAt = db.Column(db.DateTime, nullable=False, default=datetime.now())
    updatedAt = db.Column(db.DateTime, nullable=False, default=datetime.now())

    def __repr__(self):
        return '<Cities %r>' % self.name


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
            cUser = Users.query.get(data['id'])
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

    user = Users.query.filter_by(username=username).first()
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
    return {"result": True, "user":cUser.username, "name": cUser.name}

@app.route("/updateUser", methods=['POST'])
@token_required
def updateUser(cUser):
    d = request.get_json()
    hashed_pw = generate_password_hash(d['data']['password'], "sha256")
    
    cUser.username = d['data']['username']
    cUser.password = hashed_pw
    db.session.commit()
    
    return {"result": True, "message": "Successfully Updated!"}


@app.route("/getAgentFromId", methods=['POST'])
@token_required
def getAgentFromId(cUser):
    d = request.get_json()
    id = d.get('id')
    r = Agents.query.get(id)

    obj = []
    obj.insert(0, {"_id": r.id, "email": r.email, "firstName": r.firstName, "middleName": r.middleName, "lastName": r.lastName,
                    "suffix": r.suffix, "officeName": r.officeName, "officeAddress1": r.officeAddress1, "officeAddress2": r.officeAddress2,
                    "officeCity": r.officeCity, "officeState": r.officeState, "officeZip": r.officeZip, "officeCountry": r.officeCountry,
                    "officePhone": r.officePhone, "officeFax": r.officeFax, "cellPhone": r.cellPhone, "createdAt":r.createdAt})

    return {"result": True, "data": obj}


@app.route("/updateAgentInfo", methods=['PUT'])
@token_required
def updateAgentInfo(cUser):
    d = request.get_json()
    data = d.get('data')
    id = d.get('id')

    r = Agents.query.get(id)

    r.email = data['email']
    r.firstName = data['firstName']
    r.middleName = data['middleName']
    r.lastName = data['lastName']
    r.suffix = data['suffix']
    r.officeName = data['officeName']
    r.officeAddress1 = data['officeAddress1']
    r.officeAddress2 = data['officeAddress2']
    r.officeCity = data['officeCity']
    r.officeState = data['officeState']
    r.officeZip = data['officeZip']
    r.officeCountry = data['officeCountry']
    r.officePhone = data['officePhone']
    r.officeFax = data['officeFax']
    r.cellPhone = data['cellPhone']
    db.session.commit()


    return {"result": True, "message": "Successfully Updated!"}


@app.route("/removeAgent", methods=['POST'])
@token_required
def removeAgent(cUser):
    d = request.get_json()
    id = d.get("id")
    agent = Agents.query.get(id)

    db.session.delete(agent)
    db.session.commit()
    
    return {"result": True, "message": "Successfully removed!"}


@app.route("/addNewAgent", methods=["POST"])
@token_required
def addNewAgent(cUser):
    data = request.get_json()
    d = data.get('data')

    agent = Agents(email = d['email'], firstName = d['firstName'],middleName = d['middleName'],
                    lastName = d['lastName'],suffix = d['suffix'],officeName = d['officeName'],officeAddress1 = d['officeAddress1'],
                    officeAddress2 = d['officeAddress2'],officeCity = d['officeCity'],officeState = d['officeState'],
                    officeZip = d['officeZip'],officeCountry = d['officeCountry'],officePhone = d['officePhone'],
                    officeFax = d['officeFax'],cellPhone = d['cellPhone'])
    
    
    db.session.add(agent)
    db.session.commit()
    return {"result": True, "message": "New agent successfully added"}



@app.route("/getRealtors", methods=['POST', 'GET'])
@token_required
def getRealtors(cUser):
    page = request.args.get("page", type=int)
    per_page = request.args.get("per_page", type=int)
    sort = request.args.get("sort")
    isDesc = request.args.get("isDesc", type=int)
    city = request.args.get("city")
    state = request.args.get("state")
    search = request.args.get("search")

    obj = []
    cnt = 0

    if city and not state and not search:
        query = Agents.query.filter(Agents.officeCity==city)
    elif not city and state and not search:
        query = Agents.query.filter(Agents.officeState==state)
    elif city and state and not search:
        query = Agents.query.filter(Agents.officeCity==city).filter(Agents.officeState==state)
    elif search:
        agents = Agents.query
        #query = agents.filter(Agents.officeCity.ilike('%' + search + '%'))

        # search for state
        if len(search) == 2:
            query = agents.filter(Agents.officeState.ilike('%' + search + '%'))
        
        # search for email
        elif search.__contains__('@') or search.__contains__('.com') or search.__contains__('.net'):
            query = agents.filter(Agents.email.ilike('%' + search + '%'))

        # search for numbers
        elif any(char.isdigit() for char in search) and len(search) != 2:

            query = agents.filter(
                or_(
                    Agents.officePhone.ilike('%' + search + '%'),
                    Agents.cellPhone.ilike('%' + search + '%'),
                )
            )

        # search for all
        else:
            query = agents.filter(
                or_(
                    Agents.officeCity.ilike('%' + search + '%'),
                    Agents.firstName.ilike('%' + search + '%'),
                    Agents.lastName.ilike('%' + search + '%')
                )
            )
    else:
        if sort == "email":
            if isDesc:
                query = Agents.query.order_by(Agents.email.desc())
            else:
                query = Agents.query.order_by(Agents.email.asc())
        elif sort == "firstName":
            if isDesc:
                query = Agents.query.order_by(Agents.firstName.desc())
            else:
                query = Agents.query.order_by(Agents.firstName.asc())
        elif sort == "lastName":
            if isDesc:
                query = Agents.query.order_by(Agents.lastName.desc())
            else:
                query = Agents.query.order_by(Agents.lastName.asc())
        elif sort == "officeName":
            if isDesc:
                query = Agents.query.order_by(Agents.officeName.desc())
            else:
                query = Agents.query.order_by(Agents.officeName.asc())
        elif sort == "officeCity":
            if isDesc:
                query = Agents.query.order_by(Agents.officeCity.desc())
            else:
                query = Agents.query.order_by(Agents.officeCity.asc())
        elif sort == "officeState":
            if isDesc:
                query = Agents.query.order_by(Agents.officeState.desc())
            else:
                query = Agents.query.order_by(Agents.officeState.asc())
        elif sort == "officePhone":
            if isDesc:
                query = Agents.query.order_by(Agents.officePhone.desc())
            else:
                query = Agents.query.order_by(Agents.officePhone.asc())
        else:
            query = Agents.query.order_by(Agents.id)

    realtors = query.paginate(page=page, per_page=per_page)

    if not sort:
        realtors.items.sort(key=lambda x: x.id, reverse=False)

    for r in realtors.items:
        obj.insert(cnt, {"_id": r.id, "email": r.email, "firstName": r.firstName, "middleName": r.middleName, "lastName": r.lastName,
                        "suffix": r.suffix, "officeName": r.officeName, "officeAddress1": r.officeAddress1, "officeAddress2": r.officeAddress2,
                        "officeCity": r.officeCity, "officeState": r.officeState, "officeZip": r.officeZip, "officeCountry": r.officeCountry,
                        "officePhone": r.officePhone, "officeFax": r.officeFax, "cellPhone": r.cellPhone, "createdAt":r.createdAt})

        cnt += 1

    return {"realtors":obj, "page":page, "pages":realtors.pages, "next_page":realtors.next_num, "prev_page": realtors.prev_num, "total": realtors.total}



@app.route("/getCities", methods=['GET', 'POST'])
def getCities():
    d = request.args.get('state')
    state = States.query.filter_by(name=d).first()
    cities = Cities.query.filter(Cities.stateId==state.id).order_by(Cities.name).all()
    obj = []
    cnt = 0

    for c in cities:
        obj.insert(cnt, {"id": c.id, "stateId": c.stateId,"name": c.name})
        cnt += 1

    return {"result":True, "cities": obj}


@app.route("/getStates", methods=['GET', 'POST'])
def getStates():
    states = States.query.all()
    obj = []
    cnt = 0

    for s in states:
        obj.insert(cnt, {"id": s.id, "name": s.name, "longName": s.longName})
        cnt += 1

    return {"result":True, "states": obj}


#Insert mockdata to database 
'''with open("MOCKDATA/Book1.csv", "r") as csv_file:
    csv_reader = csv.DictReader(csv_file, delimiter=',')    
    cnt = 0

    for c in csv_reader:
        #if cnt < 100000:
        cnt +=1
        print(cnt)
        realtor = Agents(email=c['Email'], firstName=c['First Name'], middleName=c['Middle Name'], lastName=c['Last Name'], 
                          suffix=c['Suffix'], officeName=c['Office Name'], officeAddress1=c['Office Address1'], officeAddress2=c['Office Address2'],
                          officeCity=c['Office City'], officeState=c['Office State'], officeZip=c['Office Zip'], officeCountry=c['Office County'],
                          officePhone=c['Office Phone'], officeFax=c['Office Fax'], cellPhone=c['Cell Phone'], createdAt=datetime.now())
        db.session.add(realtor)
        db.session.commit()
        #else:
        #    break

    print("Total realtors added: ")
    print(cnt)'''


'''with open("MOCKDATA/Cities.csv", "r") as csv_file:
    csv_reader = csv.DictReader(csv_file, delimiter=',')    
    cnt = 0

    for c in csv_reader:

        cnt +=1
        cities = Cities(name=c['officeCity'])

        print(cnt)

        db.session.add(cities)
        db.session.commit()


    print("Total realtors added: ")
    print(cnt)'''



'''with open("MOCKDATA/States.csv", "r") as csv_file:
    csv_reader = csv.DictReader(csv_file, delimiter=',')    
    cnt = 0

    for c in csv_reader:

        cnt +=1
        state = States(name=c['name'], longName=c['longName'])
        db.session.add(state)
        db.session.commit()
        print(cnt)


    print("Total realtors added: ")
    print(cnt)'''


'''with open("MOCKDATA/stateCityCompresedP2.csv", "r") as csv_file:
    csv_reader = csv.DictReader(csv_file, delimiter=',')    
    cnt = 0

    for c in csv_reader:
        state = States.query.filter_by(name=c['State']).first()
        has_city = Cities.query.filter_by(name=c['City']).filter_by(stateId=state.id).first()

        if state and not has_city:
            cnt +=1
            cities = Cities(name=c['City'], stateId=state.id)

            print(cnt)

            db.session.add(cities)
            db.session.commit()


    print("Total Cities added: ")
    print(cnt)'''


if __name__ == '__main__':
    app.run(debug=True, port=6001)