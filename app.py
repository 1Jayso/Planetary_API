from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message
import os


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'planets.db')
app.config['JWT_SECRET_KEY'] = "Great" #Dont use this key in real life
app.config['MAIL_SERVER']='smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False




db = SQLAlchemy(app)
ma  = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)

@app.cli.command('create_db')
def db_create():
    db.create_all()
    print("Database created!")
    

@app.cli.command('drop_db')
def db_drop():
    db.drop_all()
    print("Database dropped!")

@app.cli.command('seed_db')
def db_seed():
    mercury = Planet(planet_name ="Mercury",
                      planet_type = "Class D",
                      home_star = "Sol",
                      mass = 3.258e23,
                      radius = 1516,
                      distance = 35.98e6)


    venus = Planet(planet_name ="Venus",
                      planet_type = "Class K",
                      home_star = "Sol",
                      mass = 4.867e24,
                      radius = 3760,
                      distance = 67.24e6)

    
    earth = Planet(planet_name ="Earth",
                      planet_type = "Class M",
                      home_star = "Sol",
                      mass = 5.972e24,
                      radius = 3959,
                      distance = 92.96e6)
    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    test_user = User(first_name = "William", 
                    last_name = "Herschel",
                    email = "test@user.com",
                    password = "p@assword")
    db.session.add(test_user)
    db.session.commit()
    print("Databae seeded!")
                    












@app.route('/')
def hello_world():
    return "Hello World!"

@app.route('/super_simple')
def super_simple():
    return jsonify(message = "Hello from Planetary API."),  200

@app.route('/not_found')
def not_found():
    return jsonify(message="The resource was not foumd"),404

@app.route('/parameters')
def parameters():
    name = request.args.get('name')
    age = int(request.args.get('age'))
    if age < 18:
        return jsonify(message="Sorry " + name +  ", you are not old enough."), 401  
    else:
        return jsonify(message="Welcome " + name + ", you are old enough.")

@app.route('/url_variables/<string:name>/<int:age>')
def url_variables(name:str, age:int):
    if age > 18:
        return jsonify(message="Welcome " + name + ", you are old enough")
    return jsonify(message="Sorry " + name +  ", you are not old enough")


@app.route('/planets', methods=['GET'])
def planets():
    planet_list = Planet.query.all()
    results = planets_schema.dump(planet_list)
    return jsonify(data=results)


@app.route ('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    test = User.query.filter_by(email=email).first()
    if test:
        return jsonify(message = "That email already exist!"),409
    else:
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        password = request.form.get('password')
        user = User(email=email, first_name=first_name, 
                    last_name=last_name, password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify(message="User has been registered!"), 201

@app.route('/login', methods=["POST"])
def login():
    if request.is_json:
        email = request.json.get('email')
        password = request.json.get('password')
    else:
        email = request.form.get('email')
        password = request.form.get('password')

    test = User.query.filter_by(email=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message="Login succesful! ", access_token=access_token), 201
    else:
        return jsonify(message="Bad email or password"), 401
        

@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email: str):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message("Your planetary API passowrd is " + user.password, 
                        sender="adodey1@gmail.com", recipients=[email])
        mail.send(msg)
        return jsonify(message="Password sent to " + email)
    return jsonify(message="That email doesn't exist"), 404


@app.route('/planet_details/<int:planet_id>', methods=["GET"])
def planet_details(planet_id: int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()

    if planet:
        result = planet_schema.dump(planet)
        return jsonify(data=result)
    else:
        return jsonify(Message="That planet doesn't exist!"), 404


@app.route('/add_planet', methods=["POST"])
def add_planet():
    planet_name = request.form.get('planet_name')
    test = Planet.query.filter_by(planet_name=planet_name).first()
    if test:
        return jsonify(Message="There is already a planet by the name " + planet_name), 409
    else:
        planet_type = request.form.get('planet_type')
        home_star = request.form.get('home_star')
        mass = float(request.form.get('mass'))
        distance = float(request.form.get('distance'))
        radius = float(request.form.get('radius'))

        new_planet = Planet(planet_name=planet_name, planet_type=planet_type, home_star=home_star, 
                            mass=mass, distance=distance, radius=radius)
        db.session.add(new_planet)
        db.session.commit()
       
        return jsonify(Message= planet_name + " has succesfully been added "), 201


class User(db.Model):
    ___tablename__ = "users"
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class Planet(db.Model):
    __tablename__="planets"
    planet_id = Column(Integer, primary_key=True)
    planet_name = Column(String)
    planet_type = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name',
                 'email', 'password')


class PlanetSchema(ma.Schema):
    class Meta:
        fields = ('planet_id', 'planet_name', 'planet_type',
                 'home_star', 'mass','radius', 'distnace')

user_schema = UserSchema()
users_schema = UserSchema(many=True)

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)









        
if __name__ == '__main__':
    app.run(debug=True)