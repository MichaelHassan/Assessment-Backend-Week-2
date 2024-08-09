"""An API for handling marine experiments."""

from datetime import datetime

from flask import Flask, jsonify, request
from psycopg2 import sql

from database_functions import get_db_connection


app = Flask(__name__)

"""
For testing reasons; please ALWAYS use this connection.
- Do not make another connection in your code
- Do not close this connection
"""
conn = get_db_connection("marine_experiments")


@app.get("/")
def home():
    """Returns an informational message."""
    return jsonify({
        "designation": "Project Armada",
        "resource": "JSON-based API",
        "status": "Classified"
    })


@app.route("/subject", methods=["GET"])
def subjects():
    """Returns an subjects"""

    query = """
            SELECT
            s.subject_id, s.subject_name, sp.species_name , s.date_of_birth
            FROM subject AS s
            JOIN species AS sp
            ON s.species_id = sp.species_id
            ORDER BY s.date_of_birth DESC
            ;
            """
    with conn.cursor() as cur:
        cur.execute(query)
        data = cur.fetchall()

    subjects = list(data)

    for subject in subjects:
        subject["date_of_birth"] = str(subject["date_of_birth"])

    return subjects, 200


@app.route("/experiment", methods=["GET"])
def experiment():
    """Returns an subjects"""

    where_case = ""

    query = """
            SELECT
            e.experiment_id, e.subject_id, sp.species_name AS species , e.experiment_date,
            et.type_name AS experiment_type , (e.score/et.max_score * 100) AS score
            FROM experiment AS e
            JOIN subject AS s
            ON s.subject_id = e.subject_id
            JOIN experiment_type AS et
            ON et.experiment_type_id = e.experiment_type_id
            JOIN species AS sp
            ON s.species_id = sp.species_id
            """

    args = request.args.to_dict()

    if args.get("type") and args.get("score_over"):
        if args.get("type") in ["intelligence", "obedience", "aggression"] and int(args.get("score_over")) >= 0 and int(args.get("score_over")) <= 100:
            where_case = f"""WHERE experiment_type = {args.get("type")} AND score > {
                args.get("score_over")} """
        else:
            return {"error": True, "message": f"Invalid value for {args.get("type")} parameter"}, 400
    elif args.get("type"):
        if args.get("type") in ["intelligence", "obedience", "aggression"]:
            where_case = f"""WHERE experiment_type = {args.get("type")}"""
        else:
            return {"error": True, "message": f"Invalid value for {args.get("type")} parameter"}, 400
    elif args.get("score_over"):
        if int(args.get("score_over")) >= 0 and int(args.get("score_over")) <= 100:
            where_case = f"""WHERE score > {args.get("score_over")} """
        else:
            return {"error": True, "message": f"Invalid value for {args.get("score_over")} parameter"}, 400

    query += where_case
    query += "\nORDER BY e.experiment_date DESC ;"

    print(query)

    with conn.cursor() as cur:
        cur.execute(query)
        data = cur.fetchall()

    experiments = list(data)

    for experiment in experiments:
        experiment["experiment_date"] = str(experiment["experiment_date"])
        experiment["score"] = f"{float(experiment["score"]):0.2f}%"

    return experiments, 200


if __name__ == "__main__":
    app.config["DEBUG"] = True
    app.config["TESTING"] = True

    app.run(port=8000, debug=True)

    conn.close()
