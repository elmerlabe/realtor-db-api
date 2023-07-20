import csv
import redis as redis_
import json
from operator import or_
import re
from functools import wraps
import jwt
from datetime import datetime
from urllib import request
from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS 
from sqlalchemy import or_, and_
from settings import DB_URI, SECRET, REDIS_URL

app = Flask(__name__)
app.secret_key = SECRET

# redis
redis = redis_.from_url(REDIS_URL)

COMMON_DOMAINS = ["gmail.com","yahoo.com","outlook.com","aol.com","icloud.com",
    "comcast.net","verizon.net","att.net","cox.net","hotmail.com",
    "spectrum.net","gmx.com","earthlink.net","juno.com","netzero.net",
    "zoho.com","protonmail.com","mail.com","tutanota.com","fastmail.com", 
    "msn.com", "live.com"]

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
CORS(app)
db = SQLAlchemy(app)


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(50))
    email = db.Column(db.String(255), nullable=False)
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
        token = None

        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

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
def getUserFromToken():

    d = request.get_json()
    token = d['token']

    if not token:
        return {"message": "a valid token is missing"}
    try:
        data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
        user = Users.query.get(data['id'])
    except:
        return {'message': 'token is invalid'}
    
    return {"result": True, "user": user.username, "name": user.name, "email": user.email}

@app.route("/updateUser", methods=['POST'])
@token_required
def updateUser(cUser):
    d = request.get_json()
    hashed_pw = generate_password_hash(d['data']['password'], "sha256")
    
    cUser.name = d['data']['name']
    cUser.email = d['data']['email']
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


@app.route("/emailCheck", methods=['GET', 'POST'])
def emailCheck():
    email = request.args.get('email')
    pat =  r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    if re.match(pat, email):
        has_email = Agents.query.filter_by(email=email).first()
        if not has_email:
            return {"result":True, "message": "Valid email format"}
        else:
            return {"result":False, "message": "Email already exist"}
    else:
        return {"result":False, "message": "Invalid email format"}


@app.route("/addNewAgent", methods=["POST"])
@token_required
def addNewAgent(cUser):
    data = request.get_json()
    d = data.get('data')
    has_email = Agents.query.filter_by(email=d['email']).first()

    if not has_email:   
        agent = Agents(email = d['email'], firstName = d['firstName'],middleName = d['middleName'],
                        lastName = d['lastName'],suffix = d['suffix'],officeName = d['officeName'],officeAddress1 = d['officeAddress1'],
                        officeAddress2 = d['officeAddress2'],officeCity = d['officeCity'],officeState = d['officeState'],
                        officeZip = d['officeZip'],officeCountry = d['officeCountry'],officePhone = d['officePhone'],
                        officeFax = d['officeFax'],cellPhone = d['cellPhone'])


        db.session.add(agent)
        db.session.commit()
        return {"result": True, "message": "New agent successfully added"}
    else:
        return {"result": False, "message": "Existing email address"}


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
    selectedColumn = request.args.get("selectedColumn")

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

        if not selectedColumn:
            # search for state
            if len(search) == 2 and not any(char.isdigit() for char in search):
                query = agents.filter(Agents.officeState.ilike('%' + search + '%'))

            # search for email
            elif search.__contains__('@') or search.__contains__('.com') or search.__contains__('.net'):
                query = agents.filter(Agents.email.ilike('%' + search + '%'))

            # search for numbers
            elif any(char.isdigit() for char in search):

                query = agents.filter(
                    or_(
                        Agents.officePhone.ilike('%' + search + '%'),
                        Agents.cellPhone.ilike('%' + search + '%'),
                    )
                )
            # search for city & state
            elif " " in search:
                txt = search.split()
                if len(txt) > 1:
                    query = agents.filter(
                        and_(
                            Agents.officeCity.ilike('%' + txt[0] + '%'),
                            Agents.officeState.ilike('%' + txt[1] + '%')
                        )
                    )
                else:
                    query = agents.filter(Agents.officeCity.ilike('%' + search + '%' ))

            # search 3 columns
            else:
                query = agents.filter(
                    or_(
                        Agents.officeCity.ilike('%' + search + '%'),
                        Agents.firstName.ilike('%' + search + '%'),
                        Agents.lastName.ilike('%' + search + '%')
                    )
                )
        else:
            if selectedColumn == "name":
                if " " in search:
                    txt = search.split() 
                    #query = Agents.query.filter(Agents.firstName==txt[0]).filter(Agents.lastName==txt[1])
                    query = agents.filter(
                        and_(
                            Agents.firstName.ilike('%' + txt[0] + '%'),
                            Agents.lastName.ilike('%' + txt[1] + '%')
                        )
                    )
                else:
                    query = agents.filter(
                        or_(
                            Agents.firstName.ilike('%' + search + '%'),
                            Agents.lastName.ilike('%' + search + '%')
                        )
                    )
            
            elif selectedColumn == "email":
                query = agents.filter(Agents.email.ilike('%' + search + '%' ))

            elif selectedColumn == "officeName":
                query = agents.filter(Agents.officeName.ilike('%' + search + '%' ))
            elif selectedColumn == "officeAddress":
                query = agents.filter(
                    or_(
                        Agents.officeAddress1.ilike('%' + search + '%' ),
                        Agents.officeAddress2.ilike('%' + search + '%' ),
                    )
                )
            elif selectedColumn == "phoneNumber":
                query = agents.filter(
                    or_(
                        Agents.officePhone.ilike('%' + search + '%' ),
                        Agents.officeFax.ilike('%' + search + '%' ),
                        Agents.cellPhone.ilike('%' + search + '%' ),
                    )
                )
            elif selectedColumn == "officeZip":
                query = agents.filter(Agents.officeZip.ilike('%' + search + '%' ))
            elif selectedColumn == "officeCity":
                query = agents.filter(Agents.officeCity.ilike('%' + search + '%' ))
            elif selectedColumn == "officeCountry":
                query = agents.filter(Agents.officeCountry.ilike('%' + search + '%' ))

        if state and not city:
            query = query.filter(Agents.officeState==state)
        elif state and city:
            query = query.filter(Agents.officeState==state).filter(Agents.officeCity==city)

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

@app.route("/getEmailDomainsCount", methods=["POST", "DELETE"])
def get_email_domains_count():
    if request.method == "DELETE":
        redis.delete("domain_map")

        return jsonify({ "success": True })

    body = request.json
    domains = body.get("domains")
    domain_map = redis.get("domain_map")

    if domain_map:
        domain_map = json.loads(domain_map)
    else:
        domain_map = {}

    for domain in domains:
        if domain not in domain_map:
            if domain in COMMON_DOMAINS:
                domain_map[domain] = '-'
            else:
                domain_map[domain] = Agents.query.filter(Agents.email.contains(domain)).count()

    redis.set("domain_map", json.dumps(domain_map))

    return jsonify(domain_map)

@app.route("/getStateAgentsCount", methods=['POST', 'DELETE'])
def get_state_agents_count():
    
    if request.method == 'DELETE':
        redis.delete("state_map")
        return jsonify({"success": True})

    body = request.json
    states = body.get('states')
    state_map = redis.get("state_map")

    if state_map:
        state_map = json.loads(state_map)
    else:
        state_map = {}
    
    for state in states:
        if state not in state_map:
            state_map[state] = Agents.query.filter(Agents.officeState==state).count()
    
    redis.set("state_map", json.dumps(state_map))

    return jsonify(state_map)


@app.route("/exportCSV", methods=['GET', 'POST'])
def exportCSV():
    state = request.args.get('state')
    city = request.args.get('city')
    
    filename = state + "_" + city + ".csv"

    if state and not city:
        query = Agents.query.filter(Agents.officeState==state).all()
    elif city and state:
        query = Agents.query.filter(Agents.officeCity==city).filter(Agents.officeState==state).all()
    else:
        query = ""

    with open('agentData.csv', 'w', encoding='UTF8', newline='') as f:
        cnt = 0
        header = ["#", "email", "firstName", "middleName", "lastName", "suffix", "officeName", "officeAddress1", "officeAddress2",
                        "officeCity", "officeState", "officeZip", "officeCountry","officePhone", "officeFax", "cellPhone"]
        writer = csv.writer(f)
        writer.writerow(header)

        for a in query:
            cnt +=1
            data = [cnt, a.email, a.firstName, a.middleName, a.lastName, a.suffix, a.officeName, a.officeAddress1, a.officeAddress2,
                    a.officeCity, a.officeState, a.officeZip, a.officeCountry, a.officePhone, a.officeFax, a.cellPhone]
            
            writer.writerow(data)

    return send_file('agentData.csv', mimetype='text/csv', as_attachment=True,  download_name=filename)

@app.route("/getCities", methods=['GET', 'POST'])
def getCities():
    d = request.args.get('state')
    state = States.query.filter_by(name=d).first()
    cities = Cities.query.filter(Cities.stateId==state.id).order_by(Cities.name).all()
    obj = []
    cnt = 0

    for c in cities:
        if c.name != "":
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

@app.route("/getDatabaseSummary", methods=['GET', 'POST'])
def getDatabaseSummary():

    db_summary_map = redis.get("db_summary_map")

    if db_summary_map:
        db_summary_map = json.loads(db_summary_map)
    else:
        agents = Agents.query.count()
        emails = Agents.query.filter(Agents.email != "").count()
        phones = Agents.query.filter(
            or_(Agents.officePhone != "",
                Agents.cellPhone != "")
        ).count()
        db_summary_map = {"agents": agents, "emails": emails, "phones": phones}
    
    redis.set("db_summary_map", json.dumps(db_summary_map))


    return jsonify(db_summary_map)

@app.route("/getAgentsByState", methods=['GET', 'POST'])
def getAgentsByState():
    state = request.args.get("state")
    totalAgents = Agents.query.filter_by(officeState=state).count()

    return {"state": state, "totalAgents": totalAgents}
    

@app.route("/getAgentsPerState/<state>", methods=['GET', 'POST'])
@token_required
def getAgentsPerState(cUser,state):

    state_map = redis.get("state_map")

    if state_map:
        state_map = json.loads(state_map)
    else:
        state_map = {}

    if state not in state_map:
        ttlAgentPerState = Agents.query.filter(Agents.officeState == state).count()
        state_map[state] = ttlAgentPerState
        redis.set("state_map", json.dumps(state_map))
    else:
        ttlAgentPerState = state_map[state]

    return {"ttlAgentPerState": ttlAgentPerState}

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