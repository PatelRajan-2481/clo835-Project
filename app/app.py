from flask import Flask, render_template, request
from pymysql import connections
import os, random, argparse, logging
import boto3

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ----- Config from env (ConfigMap/Secrets will be provided  in k8s) -----
DBHOST = os.environ.get("DBHOST", "mysql")
DBUSER = os.environ.get("DBUSER")                 # from k8s secret
DBPWD  = os.environ.get("DBPWD")                  # from k8s secret
DATABASE = os.environ.get("DBNAME", "employees")
DBPORT = int(os.environ.get("DBPORT", "3306"))

S3_BUCKET = os.environ.get("BG_S3_BUCKET")        # from ConfigMap
S3_KEY    = os.environ.get("BG_S3_KEY")           # from ConfigMap
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

GROUP_NAME = os.environ.get("GROUP_NAME", "Rajan Patel")
GROUP_SLOGAN = os.environ.get("GROUP_SLOGAN", "Never Give Up!!")

COLOR_FROM_ENV = os.environ.get('APP_COLOR') or "lime"

# ----- Colors fallback if no image -----
color_codes = {
    "red": "#e74c3c", "green": "#16a085", "blue": "#89CFF0",
    "blue2": "#30336b", "pink": "#f4c2c2", "darkblue": "#130f40", "lime": "#C1FF9C",
}
SUPPORTED_COLORS = ",".join(color_codes.keys())
COLOR = random.choice(list(color_codes.keys()))

# ----- DB connection -----
db_conn = connections.Connection(
    host=DBHOST, port=DBPORT, user=DBUSER, password=DBPWD, db=DATABASE
)

# ----- Download BG from private S3 (uses AWS creds from env = k8s secret) -----
def download_bg():
    if not (S3_BUCKET and S3_KEY):
        logging.warning("BG image not configured")
        return None
    logging.info(f"Background URL: s3://{S3_BUCKET}/{S3_KEY}")  # required log
    s3 = boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),  # optional
    )
    os.makedirs("static", exist_ok=True)
    local_path = "static/bg.jpg"
    s3.download_file(S3_BUCKET, S3_KEY, local_path)
    return local_path

BG_LOCAL = download_bg()

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template(
        'addemp.html',
        color=color_codes[COLOR],
        bg_url="/static/bg.jpg" if BG_LOCAL else None,
        group=GROUP_NAME, slogan=GROUP_SLOGAN
    )

@app.route("/about", methods=['GET','POST'])
def about():
    return render_template(
        'about.html',
        color=color_codes[COLOR],
        bg_url="/static/bg.jpg" if BG_LOCAL else None,
        group=GROUP_NAME, slogan=GROUP_SLOGAN
    )

@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    primary_skill = request.form['primary_skill']
    location = request.form['location']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()
    try:
        cursor.execute(insert_sql,(emp_id, first_name, last_name, primary_skill, location))
        db_conn.commit()
        emp_name = f"{first_name} {last_name}"
    finally:
        cursor.close()

    return render_template(
        'addempoutput.html',
        name=emp_name,
        color=color_codes[COLOR],
        bg_url="/static/bg.jpg" if BG_LOCAL else None,
        group=GROUP_NAME, slogan=GROUP_SLOGAN
    )

@app.route("/getemp", methods=['GET', 'POST'])
def GetEmp():
    return render_template(
        "getemp.html",
        color=color_codes[COLOR],
        bg_url="/static/bg.jpg" if BG_LOCAL else None,
        group=GROUP_NAME, slogan=GROUP_SLOGAN
    )

@app.route("/fetchdata", methods=['POST'])
def FetchData():
    emp_id = request.form['emp_id']
    select_sql = "SELECT emp_id, first_name, last_name, primary_skill, location from employee where emp_id=%s"
    cursor = db_conn.cursor()
    try:
        cursor.execute(select_sql, (emp_id,))
        result = cursor.fetchone()
        if not result:
            return "Employee not found", 404
        output = dict(emp_id=result[0], first_name=result[1], last_name=result[2],
                      primary_skills=result[3], location=result[4])
    finally:
        cursor.close()

    return render_template(
        "getempoutput.html",
        id=output["emp_id"], fname=output["first_name"], lname=output["last_name"],
        interest=output["primary_skills"], location=output["location"],
        color=color_codes[COLOR],
        bg_url="/static/bg.jpg" if BG_LOCAL else None,
        group=GROUP_NAME, slogan=GROUP_SLOGAN
    )

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--color', required=False)
    args = parser.parse_args()
    if args.color: COLOR = args.color
    elif COLOR_FROM_ENV: COLOR = COLOR_FROM_ENV
    if COLOR not in color_codes: exit(1)

    app.run(host='0.0.0.0', port=81, debug=True)
