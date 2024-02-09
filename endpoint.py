import time
import json
import argparse
import timeout_decorator
from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth
import pandas as pd
from flask_swagger_ui import get_swaggerui_blueprint
from db import DB

app = Flask(__name__)
auth = HTTPBasicAuth()
_usr = ""
_pass = ""
_required_cols = []
_psql_db = None
pag_start_default = 1
pag_limit_default = 100
_required_cols = [
    "Date",
    "Time",
    "Gate",
    "RegNo",
    "Total Spent Time(msecs)",
    "Image save (msecs)",
]


SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = 'http://localhost:5004/swagger.json' 

@auth.verify_password
def verify_password(u, p):
    return u == _usr and p == _pass


@app.route("/set_csv", methods=["POST"])
@auth.login_required
def read_csv_file():
    if len(request.files) == 0:
        return jsonify(
            {
                "message": "This endpoint only accept CSV files.Please be sure to send csv file."
            }
        )
    is_written = False
    for key in request.files:
        file = request.files[key]
        data_by_line = file.readlines()

        headers = data_by_line[0].decode("utf-8").rstrip().split(",")
        df = pd.DataFrame(columns=headers)
        for i in range(1, len(data_by_line)):
            df.loc[len(df)] = data_by_line[i].decode("utf-8").rstrip().split(",")

        required_cols = df[_required_cols]
        (is_written, message) = _psql_db.insert_db_many(
            file_name=file, rows=required_cols.to_dict()
        )

        if not is_written:
            print(f"mismatch ERROR:{message}")
            print(
                f"The given file:{key} will be ignored because data type does not match with the table"
            )

    return (
        jsonify(
            {"message": "The given files acceptable ones is written to the database"}
        )
        if is_written
        else jsonify(
            {
                "message": "The given files will be ignored because data type does not match with the table"
            }
        )
    )

@app.route('/swagger.json')
def swagger():
    with open('./swagger.json', 'r') as f:
        return jsonify(json.load(f))


@app.route("/get_data", methods=["GET"])
@auth.login_required
def get_data():
    start = (
        int(request.args.get("set"))
        if request.args.get("set") is not None
        and request.args.get("set").isdigit()
        and int(request.args.get("set")) != 0
        else pag_start_default
    )
    limit = (
        int(request.args.get("limit"))
        if request.args.get("limit") is not None and request.args.get("limit").isdigit()
        else pag_limit_default
    )
    readed_data = _psql_db.get_db_data(start, limit, _required_cols)

    return jsonify(readed_data)

@timeout_decorator.timeout(300, timeout_exception=ConnectionError)
def db_connect(host, port, db, password):
    global _psql_db
    while True:
        try:
            _psql_db = DB(host=host, port=port, password=password, user=db)
            print(f"Database connection to{host}:{port} is succesfull")
            return
        except ConnectionError:
            time.sleep(0.5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", action="store", default="0.0.0.0")
    parser.add_argument("--port", action="store", default="5003")
    parser.add_argument("-u", "--authuser", action="store", default="basicuser")
    parser.add_argument("-p", "--password", action="store", default="mkuhA4HfTYtr")
    parser.add_argument("-pp", "--postgres_port", action="store", default="5432")
    parser.add_argument("-ph", "--postgres_host", action="store", default="192.168.1.5")
    parser.add_argument("--postgres_password", action="store", default="Password7")
    parser.add_argument("--user", action="store", default="postgres")

    args = parser.parse_args()
    _usr = args.authuser
    _pass = args.password
    try:
        db_connect(
            host=args.postgres_host,
            port=args.postgres_port,
            password=args.postgres_password,
            db=args.user,
        )
    except Exception as e:
        print(
            f"Exception {e} is occured while trying to connect to the postgres database"
        )
        exit(1)

    swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Test application"
    }
    )
    app.register_blueprint(swaggerui_blueprint)
    app.run(host=args.host, port=int(args.port))
