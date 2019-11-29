
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
import random
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@35.243.220.243/proj1part2
#
# For example, if you had username gravano and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://gravano:foobar@35.243.220.243/proj1part2"
#
DATABASEURI = "postgresql://sy2650:8683@35.243.220.243/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
#
#engine.execute("""CREATE TABLE IF NOT EXISTS test1 (
#  id serial,
#  name text
#);""")
#engine.execute("""INSERT INTO test1(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")
#"""

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print(request.args)


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT uni FROM users")
  names = []
  
  for result in cursor:
    names.append(result['uni'])
    #unis.append(result['uni'])# can also be accessed using result[0]
  cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/another')
def another():
  return render_template("another.html");

@app.route('/advSearch')
def advSearch():
    return render_template("advSearch.html");

@app.route('/dbbrowse_by_major',methods=['GET','POST'])
def dbbrowse_by_major():
    major = request.form['majors']
	
    g.conn.execute('INSERT INTO searchedUni(uni) VALUES(%s)', major)
    cursor = g.conn.execute(""" SELECT m.uni
        		    	    FROM majors_in m, searchedUni sm
	       			    WHERE m.major_name = sm.uni
		    			""")
    output = []
    for result in cursor:
    	output.append(result['uni'])
    cursor.close()
    context=dict(majors=output)
    g.conn.execute("DELETE FROM searchedUni")
    return render_template("advSearch.html",**locals(),**context);


@app.route('/dbbrowse_by_school', methods=['GET','Post'])
def dbbrowse_by_school():
    school = request.form['schools']
    g.conn.execute('INSERT INTO searchedUni(uni) VALUES(%s)', school)
    cursor = g.conn.execute("""SELECT s.uni
                                FROM users s, searchedUni u
                                WHERE s.school_name = u.uni""")

    output_school=[]
    for result in cursor:
        output_school.append(result['uni'])
    cursor.close()
    g.conn.execute("DELETE FROM searchedUni")
    context=dict(schools=output_school)
    return render_template("advSearch.html",**locals(),**context);


# Example of adding new data to the database
@app.route('/adduser', methods=['GET','POST'])
def adduser():


    if "uni" and "school_name" in request.form:
        name= request.form['name']
        if name == '' or name == null:
        	name = "NULL"
        uni= request.form['uni']
        school_name=request.form['school_name']
        major_name = request.form['major_name']
        
        club_name = request.form['club_name']
        since = request.form['since']
        if club_name == ' ' or club_name == null:
            club_name = 'NULL'
        if since=='' or since ==null:
            since = 'NULL'
        hobby_name = request.form['hobby_name']
        if hobby_name == ' ' or hobby_name == null:
            hobby_name = 'NULL'
        work_field = request.form['work_field']
        if work_field == '' or work_field == null:
        	work_field = 'NULL'
        gender = request.form['gender']
        if gender =='' or gender == null:
        	gender = 'Undisclosed'
        bio = request.form['bio']
        if bio =='' or bio == null:
        	bio = 'NULL'
        age = request.form['age']
        phone_number = request.form['phone_number']
        if phone_number =='' or phone_number == null:
        	phone_number= "NULL" 
        email = request.form['email']
        location = request.form['location']
        if location =='' or location == null:
        	location = 'NULL'
        graduation_year= request.form['graduation_year']
        
        
        g.conn.execute('INSERT INTO users (name,uni, school_name, work_field, gender, bio, age, phone_number, email, location, graduation_year) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', name, uni, school_name, work_field, gender, bio, age, phone_number, email, location, graduation_year)        
        if club_name != 'NULL':
            g.conn.execute('INSERT INTO is_in(uni, club_name) VALUES(%s, %s)', uni, club_name)
        if hobby_name != 'NULL':
            g.conn.execute('INSERT INTO interested_in(uni, hobby_name) VALUES(%s, %s)', uni, hobby_name)
        if major_name !='NULL':
            g.conn.execute('INSERT INTO majors_in(uni, major_name) VALUES(%s,%s)', uni, major_name)
        
       
        user=[name,uni,school_name, work_field, gender, bio, age, phone_number, email, location, graduation_year]
        
        print(user);
        
        cursor = g.conn.execute("SELECT uni FROM users")
        names = []
        for result in cursor:
            names.append(result['uni'])
        cursor.close()
        
        for x in range(1):
            temp = random.randint(1,560)
        
        for x in range(1):
            comp_val = random.randint(1,100); 

        for n in names:
            g.conn.execute('INSERT INTO users_is_compatible(uni, gender, work_field, age, phone_number, email, bio, comparison_number,  compatability_score, other_user) VALUES(%s, %s, %s, %s, %s, %s, %s,%s, %s, %s)', uni, gender, work_field, age, phone_number, email, bio, temp, comp_val, n)
            for x in range(1):
                comp_val = random.randint(1,100);

    return render_template("adduser.html", **locals());

@app.route('/findMatch', methods = ['GET', 'POST'])
def findMatch():

    matchUni = request.form['uni']

    g.conn.execute("INSERT INTO searchedUni(uni) VALUES(%s)", matchUni)

    outputA = []
    
    cursor = g.conn.execute("""SELECT *
                               FROM users u, searchedUni u1
                               WHERE u1.uni = u.uni""")

    for result in cursor:
        outputA.append(result['name'])
        outputA.append(result['uni'])
        outputA.append(result['work_field'])
        outputA.append(result['school_name'])
        outputA.append(result['gender'])
        outputA.append(result['bio'])
        outputA.append(result['age'])
        outputA.append(result['phone_number'])
        outputA.append(result['email'])
    cursor.close()

    g.conn.execute("""DELETE FROM searchedUni""")

    return render_template("findMatch.html", **locals());


@app.route('/yourInfo', methods = ['GET', 'POST'])
def yourInfo():
    
    uniYour = request.form['uni']

    g.conn.execute("INSERT INTO searchedUni(uni) VALUES(%s)", uniYour)
   
    print(uniYour); 

    cursor8 = g.conn.execute("""SELECT *
                               FROM users u, searchedUni u1
                               WHERE u1.uni = u.uni""")

    outputA1 = []
    for result in cursor8:
        outputA1.append(result['uni'])
        outputA1.append(result['name'])
        outputA1.append(result['work_field'])
        outputA1.append(result['school_name'])
        outputA1.append(result['gender'])
        outputA1.append(result['bio'])
        outputA1.append(result['age'])
        outputA1.append(result['phone_number'])
        outputA1.append(result['email'])
        #outputA1.append(result['club_name'])
        #outputA1.append(result['hobby_name'])
    cursor8.close()

    print(outputA1)
    context1 = dict(outputA = outputA1) 
    outputB2 = []

    #g.conn.execute("""DROP VIEW reviewvals""")

    #g.conn.execute("""CREATE VIEW reviewvals AS SELECT r.review_of_1 
     #                   FROM searchedUni u, reviews r
      #                  WHERE r.uni_1 = u.uni UNION ALL
       #                 SELECT r2.review_of_2 FROM reviews r2, searchedUni u1
        #                WHERE r2.uni_2 = u1.uni""")

    #g.conn.execute("""CREATE VIEW rv1 AS SELECT AVG(r.review_of_1) FROM reviewvals r""")
    #cursor3 = g.conn.execute("""SELECT * FROM rv1""")
    
    #outputC4 = []
    #for result in cursor3:
    #    outputC4.append(result['AVG(review_of_1)'])
    #cursor3.close()

    #g.conn.execute("""DROP VIEW rv1""")
    #g.conn.execute("""DROP VIEW reviewvals CASCADE""")

    cursor1 = g.conn.execute("""SELECT r.review_of_1 FROM reviews r, searchedUni u1
WHERE r.uni_1 =  u1.uni""")
    
    
    for result in cursor1:
        outputB2.append(result['review_of_1'])
    cursor1.close()
    context2 = dict(outputB=outputB2)

    outputC3 = []
    #do w review of 2
    cursor2 = g.conn.execute("""SELECT r.review_of_2  FROM reviews r, searchedUni u1
    WHERE r.uni_2 = u1.uni""")

    for result in cursor2:
        outputC3.append(result['review_of_2'])
    cursor2.close()
    context3 = dict(outputC=outputC3)

    cursor3 = g.conn.execute("""SELECT m.date, m.location, m.length, m2.uni
                                FROM meet_up m, met_up m1, met_up m2, searchedUni u1
                                WHERE m.meet_up_number = m1.meet_up_number AND m1.uni = u1.uni AND m2.meet_up_number = m1.meet_up_number AND m2.uni != m1.uni""")

    outputD4 = []
    #outputD5 = []
    #outputD6 = []
    #outputD7 = []

    for result in cursor3:
        outputD4.append(result['date'])
        outputD4.append(result['location'])
        outputD4.append(result['length'])
        outputD4.append(result['uni'])
    cursor3.close()
    context4= dict(outputD=outputD4)#, outputE=outputD5,outputF=outputD6,outputG=outputD7)

    g.conn.execute("""DELETE FROM searchedUni""")

    return render_template("yourInfo.html", **locals(),**context1,**context2, **context3, **context4);
import random



@app.route('/addReview',methods=['GET','POST'])
def addReview():
    #yourUni= form.request["yourUni"]
    uni=request.form["uni"]
    yourUni=request.form["yourUni"]
    score=request.form["score"]
    #location = form.request["location"]
    #date = form.request["date"]
    cursor=g.conn.execute("SELECT DISTINCT m1.meet_up_number FROM met_up m1, met_up m2 WHERE m1.uni=%s AND m2.uni=%s",uni,yourUni)
    match_number=[]
    for result in cursor:
       match_number.append(result['meet_up_number'])
    cursor.close()
    g.conn.execute("INSERT INTO Reviews(uni_1,uni_2,review_of_2, match_number, meet_up_number) Values(%s,%s,%s,%s,%s)",yourUni, uni, score, match_number[0], match_number[0])
    g.conn.execute("INSERT INTO was_rated(uni,match_number) Values(%s,%s),(%s,%s)",uni,match_number[0],yourUni,match_number[0])
    return render_template("addReview.html", **locals());

@app.route('/addMeet', methods=['get','post'])
def addMeet():
    uni=request.form["uni2"]
    yourUni=request.form["yourUni2"]
    meet_up_number=request.form["meet_up_number"]
    date=request.form["date"]
    location=request.form["location"]
    length=request.form["length"]
    
    g.conn.execute("""INSERT INTO meet_up(meet_up_number, date, location, length)
                      Values(%s,%s,%s,%s)""",meet_up_number,date,location,length)
    g.conn.execute("""INSERT INTO met_up(meet_up_number,uni)
                        Values(%s,%s),(%s,%s)""",meet_up_number,yourUni,
                        meet_up_number,uni)
    #g,conn.execute("INSERT INTO was")
    return render_template("addReview.html",**locals());


@app.route('/possibleClubs', methods = ['GET', 'POST'])
def possibleClubs():
    cursor4 = g.conn.execute("""SELECT c.club_name
                               FROM clubs c""")
    outputE = []
    for result in cursor4:
        outputE.append(result['club_name'])
    cursor4.close()

    return render_template("possibleClubs.html", **locals()); 

@app.route('/inOrchesis', methods = ['GET', 'POST'])
def inOrchesis():
    cursor5 = g.conn.execute("""SELECT u.uni, u.name
                                FROM users u, is_in c
                                WHERE u.uni  = c.uni AND c.club_name = 'Orchesis'""")

    outputQ = [] 
    for result in cursor5:
        outputQ.append(result['uni'])
        outputQ.append(result['name'])
    cursor5.close()

    return render_template("inOrchesis.html", **locals()); 

@app.route('/possibleHobbies', methods = ['GET', 'POST'])
def possibleHobbies():
    cursor5 = g.conn.execute("""SELECT h.hobby_name
                                FROM hobbies h""")
    outputF = []
    for result in cursor5:
        outputF.append(result['hobby_name'])
    cursor5.close()

    return render_template("possibleHobbies.html", **locals()); 

@app.route('/Dance', methods = ['GET', 'POST'])
def Dance():
    cursor5 = g.conn.execute("""SELECT u.uni, u.name
                                FROM users u, interested_in c
                                WHERE u.uni  = c.uni AND c.hobby_name = 'Dance'""")

    outputQ = []
    for result in cursor5:
        outputQ.append(result['uni'])
        outputQ.append(result['name'])
    cursor5.close()

    return render_template("Dance.html", **locals());

@app.route('/ComputerScience', methods = ['GET', 'POST'])
def ComputerScience():
    cursor5 = g.conn.execute("""SELECT u.uni, u.name
                                FROM users u, majors_in c
                                WHERE u.uni  = c.uni AND c.major_name = 'Computer Science'""")

    outputQ = []
    for result in cursor5:
        outputQ.append(result['uni'])
        outputQ.append(result['name'])
    cursor5.close()

    return render_template("ComputerScience.html", **locals());

@app.route('/possibleMajors', methods = ['GET', 'POST'])
def possibleMajors():
    cursor6 = g.conn.execute("""SELECT m.major_name
                                FROM major m""")

    outputF = [] 
    for result in cursor6:
        outputF.append(result['major_name'])
    cursor6.close()

    return render_template("possibleMajors.html", **locals()); 

@app.route('/majorisin',  methods = ['GET', 'POST'])
def majorisin():
    cursor6 = g.conn.execute("""SELECT m.school_name
                                FROM m_is_in m
                                WHERE m.major_name = 'Computer Science'""")
    outputF = []
    for result in cursor6:
        outputF.append(result['school_name'])
    cursor6.close()

    return render_template("majorisin.html", **locals());

@app.route('/CUSchools', methods = ['GET', 'POST'])
def CUSchools():
    cursor6 = g.conn.execute("""SELECT s.school_name
                                FROM CU_school s""")

    outputF = []
    for result in cursor6:
        outputF.append(result['school_name'])
    cursor6.close()

    return render_template("CUSchools.html", **locals());


@app.route('/selectUni', methods = ['GET', 'POST'])
def selectUni():
    
    uni = request.form['uni']

    g.conn.execute("INSERT INTO searchedUni(uni) VALUES(%s)", uni)

    cursor = g.conn.execute("""SELECT DISTINCT u.uni, u.other_user, u.compatability_score
                                FROM  users_is_compatible u, searchedUni v
                                WHERE v.uni = u.uni
                                ORDER BY u.compatability_score DESC""")

    output = []
    output1 = []
    output2 = []
    for result in cursor:
        output.append(result['uni'])
        output1.append(result['other_user'])
        output2.append(str(result['compatability_score']))
    cursor.close()

    #g.conn.execute("""DELETE FROM searchedUni WHERE uni = (SELECT MAX(uni) FROM searchedUni)""")

    g.conn.execute("""DELETE FROM searchedUni""")

    return render_template("uniInfo.html", **locals()); 


    #uni1 = uni
    #context = dict(data = uni1)
    #return render_template("uniInfo.html", )


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
