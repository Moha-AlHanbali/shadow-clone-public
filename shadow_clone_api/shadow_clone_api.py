"""This module handles API requests"""

from distutils.log import error
from datetime import datetime
import os, requests, json, shutil

import werkzeug
from dotenv import load_dotenv
from flask import (
    Flask,
    request,
    Response,
    send_file,
    abort,
    make_response,
    jsonify,
    render_template,
)
from flask_expects_json import expects_json
from jsonschema import ValidationError
from flask_sock import Sock
from shelljob import proc
from flask_jwt_extended import JWTManager, jwt_required
from flask_cors import CORS, cross_origin

from shadow_clone_api.shadow_clone import ShadowClone
from shadow_clone_api.shadow_clone_models import db, Cohorts, Students
from shadow_clone_api.shadow_clone_auth import generate_ws_jwt, tasks
from shadow_clone_api.shadow_clone_schema import (
    add_cohort_schema,
    clone_schema,
    manage_cohort_schema,
    manage_student_schema,
)


load_dotenv()
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")

app = Flask(__name__)
CORS(app)
app.config.from_object("config.DevConfig")
db.init_app(app)
sock = Sock(app)
JWTManager(app)


# NOTE: Run ShadowClone Operation
@app.route("/scan", methods=["POST"])
@cross_origin(origins="*", methods=["POST"])
@jwt_required()
@expects_json(clone_schema)
def detection_request():

    (
        MAX_THREADS,
        SIMILARITY_THRESHOLD,
        TESTS,
        CHEATER_REPORT,
        QUICK_MODE,
        LEGACY,
        EXCEL,
        course,
        owners,
        repository,
        cohort,
    ) = [setting for setting in request.get_json().values()]

    try:
        shadow_clone = ShadowClone(
            course,
            owners,
            repository,
            cohort,
            MAX_THREADS,
            SIMILARITY_THRESHOLD,
            TESTS,
            CHEATER_REPORT,
            QUICK_MODE,
            LEGACY,
            EXCEL,
        )

        REPORT_PATH = shadow_clone.operate()

        return send_file(f"../{REPORT_PATH}", as_attachment=True)

    except error:
        return Response(response=error, status=500)

@app.route("/awaken", methods=["GET"])
@cross_origin(origins="*", methods=["GET"])
def awaken_server():
    try:
        return Response(status=200)

    except error:
        return Response(response=error, status=500)

# NOTE: Returns ShadowClone Github usage status
@app.route("/status", methods=["GET"])
@cross_origin(origins="*", methods=["GET"])
@jwt_required()
def get_status():
    try:
        gh_status = requests.get(
            "https://api.github.com/rate_limit",
            headers={"Authorization": f"bearer {GITHUB_ACCESS_TOKEN}"},
        ).json()["resources"]["core"]
        return Response(response=f"<h1>{gh_status}</h1>", status=200)

    except error:
        return Response(response=error, status=500)


# NOTE: Creates a Cohort
@app.route("/cohort", methods=["POST"])
@jwt_required()
@expects_json(add_cohort_schema)
def add_cohorts():
    try:
        COHORT, COURSE, STUDENTS = [setting for setting in request.get_json().values()]

        if (
            db.session.query(Cohorts.id)
            .filter_by(cohort_id=COHORT, course=COURSE)
            .first()
        ):
            abort(
                500,
                (
                    f"Error 500: Internal Server Error. {COHORT} already exists for {COURSE} stream."
                ),
            )

        db.session.add(Cohorts(cohort_id=COHORT, course=COURSE))

        for student in STUDENTS:
            (
                db.session.add(Students(cohort_id=COHORT, github_id=student))
            ) if not db.session.query(Students.id).filter_by(
                cohort_id=COHORT, github_id=student
            ).first() else None

        db.session.commit()

        return Response(
            response=f"<h1> Created {COHORT} for {COURSE} stream with {STUDENTS} as students.</h1>",
            status=201,
        )

    except error:
        return Response(response=error, status=500)


# NOTE: Modifies/Deletes a Cohort
@app.route("/cohort", methods=["PUT", "DELETE"])
@jwt_required()
@expects_json(manage_cohort_schema)
def manage_cohorts():
    try:
        ID, COHORT, COURSE, STUDENTS = [
            setting for setting in request.get_json().values()
        ]

        if not db.session.query(Cohorts).filter_by(id=ID).first():
            abort(500, (f"Error 500: Internal Server Error. {COHORT} does not exist."))

        if request.method == "PUT":
            db.session.query(Cohorts).filter_by(id=ID).update(
                {Cohorts.cohort_id: COHORT, Cohorts.course: COURSE}
            )

            for student in STUDENTS:
                if db.session.query(Students).filter_by(id=student["id"]).first():
                    db.session.query(Students).filter_by(id=student["id"]).update(
                        {
                            Students.cohort_id: COHORT,
                            Students.github_id: student["github_id"],
                        },
                        synchronize_session=False,
                    )

            db.session.commit()
            return Response(
                response=f"<h1> Edited {COHORT} for {COURSE} stream with {STUDENTS} as students.</h1>",
                status=200,
            )

        db.session.query(Cohorts).filter_by(id=ID).delete()
        db.session.commit()

        return Response(
            response=f"<h1> Deleted {COHORT} for {COURSE} stream with all of its' enrolled students {STUDENTS}.</h1>",
            status=200,
        )

    except error:
        return Response(response=error, status=500)


# NOTE: Modifies/Deletes Students
@app.route("/student", methods=["PUT", "DELETE"])
@jwt_required()
@expects_json(manage_student_schema)
def manage_students():
    try:
        ID, COHORT, STUDENTS = [setting for setting in request.get_json().values()]

        if not db.session.query(Cohorts).filter_by(id=ID).first():
            abort(500, (f"Error 500: Internal Server Error. {COHORT} does not exist."))

        if request.method == "PUT":
            for student in STUDENTS:
                if db.session.query(Students).filter_by(id=student["id"]).first():
                    db.session.query(Students).filter_by(id=student["id"]).update(
                        {
                            Students.cohort_id: COHORT,
                            Students.github_id: student["github_id"],
                        },
                        synchronize_session=False,
                    )

            db.session.commit()

            return Response(
                response=f"<h1> Set {STUDENTS} cohort as {COHORT}.</h1>", status=200
            )

        [
            db.session.query(Students).filter_by(id=student["id"]).delete()
            for student in STUDENTS
        ]
        db.session.commit()

        return Response(
            response=f"<h1> Deleted {STUDENTS} from {COHORT} cohort.</h1>", status=200
        )

    except error:
        return Response(response=error, status=500)


# NOTE: Returns Cohorts Data
@app.route("/retrieve", methods=["GET"])
@jwt_required()
def retrieve_cohorts():
    try:
        query_data = (
            db.session.query(Cohorts, Students)
            .outerjoin(Students, Cohorts.cohort_id == Students.cohort_id)
            .all()
        )
        print(query_data)
        cohorts = dict()

        for row in query_data:
            id = row[0].id
            cohort_id = row[0].cohort_id
            course = row[0].course
            student_id = row[1].id if row[1] else None
            student = row[1].github_id if row[1] else None

            if not cohort_id in cohorts:
                cohorts[cohort_id] = {course: list(), "id": id}
            cohorts[cohort_id][course].append(
                {"student": student, "student_id": student_id}
            )

        return jsonify(cohorts)

    except:
        abort(
            500,
            (
                f"Error 500: Internal Server Error. Could not retrieve cohorts from Database."
            ),
        )


# NOTE: Error Handling
@app.errorhandler(400)
def bad_request(error):
    if isinstance(error.description, ValidationError):
        original_error = error.description
        return make_response(jsonify({"error": original_error.message}), 400)
    return f"<h1> Error 400: Bad Request!</h1><br><h4>{error}</h4>", 400


@app.errorhandler(werkzeug.exceptions.NotFound)
def handle_not_found(e):
    return "<h1> Error 404: Page Not Found!</h1>", 404


# NOTE: SEARCH AND LIST REPORTS
@app.route("/search", methods=["POST"])
@cross_origin(origins="*", methods=["POST"])
@jwt_required()
def search_reports():
    try:
        report_list = list()
        if os.path.isdir("reports"):
            for root, dirs, files in os.walk("reports"):
                for file in files:
                    if file.endswith(".csv") or file.endswith(".xlsx"):
                        report_list.append({file: f"./{root}/{file}"})

        if report_list:
            return make_response(jsonify({"report_list": report_list}), 200)

        return Response(response="<h1> No reports found</h1>", status=200)

    except:
        return Response(response=error, status=500)


# NOTE: CLEAR ALL REPORTS
@app.route("/flush_all", methods=["POST"])
@jwt_required()
def flush_all():
    try:
        if os.path.isdir("reports"):
            os.rmdir("reports")
            return Response(
                response="<h1>Flushed all existing reports</h1>", status=200
            )

        return Response(response="<h1> No reports to flush</h1>", status=200)

    except error:
        return Response(response=error, status=500)


# NOTE: DOWNLOAD ALL REPORTS
@app.route("/retrieve_all", methods=["POST"])
@cross_origin(origins="*", methods=["POST"])
@jwt_required()
def retrieve_all():
    try:
        if os.path.isdir("reports"):
            if os.path.isfile("reports_collection.zip"):
                os.remove("reports_collection.zip")

            shutil.make_archive("reports_collection", "zip", "reports")

            return send_file("../reports_collection.zip", as_attachment=True)

        return Response(response=f"<h1> No reports to retrieve</h1>", status=200)

    except error:
        return Response(response=error, status=500)


# NOTE: AUTOMATE MAILING
date_validator = list()


@app.route("/trigger", methods=["POST"])
@cross_origin(origins="*", methods=["POST"])
@jwt_required()
def trigger():
    try:
        today = datetime.today()
        today_date = today.strftime("%Y-%m-%d")
        if datetime.weekday(today) == 4 or datetime.weekday(today) == 5:
            return Response(
                response=f"<h1> Weekend, no emails to send!</h1>", status=200
            )

        if (
            not today_date in date_validator
        ):  # NOTE: Heroku waking up + retry sends 2 emails
            tasks()
            date_validator.append(today_date)
            print(date_validator)
            return Response(response=f"<h1> Emails sent!</h1>", status=200)

        return Response(response=f"<h1> Emails already sent!</h1>", status=200)
    except error:
        return Response(response=error, status=500)


# NOTE: WEBSOCKET HANDLING

# NOTE: Temporary Front-end template
@app.route("/receiver")
@cross_origin(origins="*")
def receiver():
    try:
        return render_template("receiver.html")
    except error:
        return Response(response=error, status=500)


# NOTE: Temporary WebSocket JWT Generator
@app.route("/authorize", methods=["POST"])
@cross_origin(origins="*", methods=["POST"])
@jwt_required()
def ws_jwt():
    try:
        return Response(response=generate_ws_jwt(), status=200)
    except error:
        return Response(response=error, status=500)


# NOTE: Report download request
@app.route("/report", methods=["POST"])
@cross_origin(origins="*", methods=["POST"])
@jwt_required()
def report():
    try:
        REPORT_PATH = request.form.get("REPORT_PATH")
        return send_file(f"../{REPORT_PATH}", as_attachment=True)

    except error:
        return Response(response=error, status=500)


# NOTE: Run Shadow Clone
def operate(
    course,
    owners,
    repository,
    cohort,
    MAX_THREADS,
    SIMILARITY_THRESHOLD,
    TESTS,
    CHEATER_REPORT,
    QUICK_MODE,
    LEGACY,
    EXCEL,
):
    shadow_clone = ShadowClone(
        course,
        owners,
        repository,
        cohort,
        MAX_THREADS,
        SIMILARITY_THRESHOLD,
        TESTS,
        CHEATER_REPORT,
        QUICK_MODE,
        LEGACY,
        EXCEL,
    )
    return shadow_clone.operate()


# NOTE: Verify JSON sent to Websocket operate
# HACK: Needs better verification
def verify_websocket_json(request_json):
    fields = [
        "SIMILARITY_THRESHOLD",
        "CHEATER_REPORT",
        "QUICK_MODE",
        "MAX_THREADS",
        "LEGACY",
        "TESTS",
        "EXCEL",
        "owners",
        "repository",
        "cohort",
        "course",
    ]
    data_types = [
        int,
        bool,
        bool,
        int,
        bool,
        bool,
        bool,
        list,
        str,
        str,
        str,
    ]  # NOTE : Serialization of numeric values with JSON limitation, SIMILARITY_THRESHOLD should be a float.
    try:
        # FIXME: Something like this at least
        # return True and [True and type(request_json[field]) if type(request_json[field]) == data_types[i] else None for i,field in enumerate(fields)]
        for i, field in enumerate(fields):
            if type(request_json[field]) == data_types[i]:
                continue
            else:
                return False
        return True
    except:
        return False


# NOTE: WebSocket Route
@sock.route("/stream")
@jwt_required(fresh=True, locations="query_string")
def stream(sock):
    try:
        while True:

            data = sock.receive(timeout=None)

            # NOTE: Keep connection alive
            if data == "__ping__":
                sock.send("__pong__ ")
                # print("PONG")
                continue

            json_data = json.loads(data)

            if verify_websocket_json(json_data):

                fields = [
                    "SIMILARITY_THRESHOLD",
                    "CHEATER_REPORT",
                    "QUICK_MODE",
                    "MAX_THREADS",
                    "LEGACY",
                    "TESTS",
                    "EXCEL",
                    "owners",
                    "repository",
                    "cohort",
                    "course",
                ]
                process_group = proc.Group()
                (
                    SIMILARITY_THRESHOLD,
                    CHEATER_REPORT,
                    QUICK_MODE,
                    MAX_THREADS,
                    LEGACY,
                    TESTS,
                    EXCEL,
                    owners,
                    repository,
                    cohort,
                    course,
                ) = [json_data[field] for field in fields]
                # NOTE: Import operate method, run it, passing arguments from requests
                process_group.run(
                    [
                        "python",
                        "-c",
                        f"from shadow_clone_api.shadow_clone_api import operate; operate('{course}', {owners}, '{repository}', '{cohort}', {MAX_THREADS}, {SIMILARITY_THRESHOLD}, {TESTS}, {CHEATER_REPORT}, {QUICK_MODE}, {LEGACY}, {EXCEL})",
                    ]
                )

                # FIXME: NEEDS REFACTOR
                time_stamp = datetime.fromtimestamp(
                    datetime.timestamp(datetime.now())
                ).strftime("%d-%B-%Y")
                mode = "LEGACY" if LEGACY else "NORMAL"
                REPORT_PATH = (
                    f"./reports/{cohort}/{time_stamp}/{mode}-{repository}.xlsx"
                    if EXCEL
                    else f"./reports/{cohort}/{time_stamp}/{mode}-{repository}.csv"
                )

                print("SERVER PENDING...")
                sock.send("SERVER PENDING...")
                
                while process_group.is_pending():
                    lines = process_group.readlines()

                    for proc_, line in lines:
                        # time.sleep(0.1)
                        print(line.decode("utf-8", "ignore"))
                        sock.send(line.decode("utf-8", "ignore"))

                sock.send(f"REPORT_PATH={REPORT_PATH}")
                sock.close(reason=1000, message="Process complete")

            else:
                sock.send(
                    "Error: JSON format does not match required schema. Try to give SIMILARITY_THRESHOLD an integer value if it is not already."
                )

    except:
        sock.send("Error: Problem connecting to the Websocket.")
