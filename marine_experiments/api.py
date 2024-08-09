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


@app.route("/experiment", methods=["GET", "POST"])
def experiment():
    """Returns an subjects"""

    query_none = """
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
            ORDER BY e.experiment_date DESC ;
            """

    query_both = """
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
            WHERE et.type_name ILIKE %s AND (e.score/et.max_score * 100) > %s
            ORDER BY e.experiment_date DESC ;
            """

    query_type = """
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
            WHERE et.type_name ILIKE %s
            ORDER BY e.experiment_date DESC ;
            """
    query_score = """
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
            WHERE (e.score/et.max_score * 100) > %s
            ORDER BY e.experiment_date DESC ;
            """

    if request.method == "GET":

        args = request.args.to_dict()

        if args.get("type") and args.get("score_over"):
            try:
                int(args.get("score_over"))
            except TypeError:
                return {"error": True, "error": "Invalid value for 'score_over' parameter"}, 400

            if args.get("type").lower() in ["intelligence", "obedience", "aggression"] and int(args.get("score_over")) >= 0 and int(args.get("score_over")) <= 100:
                with conn.cursor() as cur:
                    cur.execute(query_both, (args.get(
                        "type"), int(args.get("score_over"))))
                    data = cur.fetchall()
            else:
                return {"error": True, "error": f"Invalid value for 'type' parameter"}, 400
        elif args.get("type"):
            if args.get("type").lower() in ["intelligence", "obedience", "aggression"]:
                with conn.cursor() as cur:
                    cur.execute(query_type, (args.get("type"),))
                    data = cur.fetchall()
            else:
                return {"error": True, "error": "Invalid value for 'type' parameter"}, 400
        elif args.get("score_over"):
            try:
                int(args.get("score_over"))
            except Exception:
                return {"error": True, "error": "Invalid value for 'score_over' parameter"}, 400
            if int(args.get("score_over")) >= 0 and int(args.get("score_over")) <= 100:

                print(args.get("score_over"))

                with conn.cursor() as cur:
                    cur.execute(query_score, (args.get("score_over"),))
                    data = cur.fetchall()
            else:
                return {"error": True, "error": "Invalid value for 'score_over' parameter"}, 400
        else:
            with conn.cursor() as cur:
                cur.execute(query_none)
                data = cur.fetchall()

        experiments = list(data)

        for experiment in experiments:
            experiment["experiment_date"] = str(experiment["experiment_date"])
            experiment["score"] = f"{float(experiment["score"]):0.2f}%"

        return experiments, 200

    data = request.json

    if data.get("subject_id") and data.get("experiment_type") and data.get("score"):
        try:
            if type(data.get("subject_id")) != int:
                raise ValueError
            if not int(data.get("subject_id")) > 0:
                raise ValueError
        except ValueError:
            return {'error': "Invalid value for 'subject_id' parameter."}, 400

        try:
            if data.get("experiment_type").lower() not in ["intelligence", "obedience", "aggression"]:
                raise ValueError
        except Exception:
            return {"error": "Invalid value for 'experiment_type' parameter."}, 400

        try:
            int(data.get("score"))
            if type(data.get("score")) != int:
                raise ValueError
            if not int(data.get("score")) > 0:
                raise ValueError
        except Exception:
            return {'error': "Invalid value for 'score' parameter."}, 400

    if not data.get("subject_id"):
        return {'error': "Request missing key 'subject_id'."}, 400
    elif not data.get("experiment_type"):
        return {'error': "Request missing key 'experiment_type'."}, 400
    elif not data.get("score"):
        return {'error': "Request missing key 'score'."}, 400

    return {}, 201


@ app.route("/experiment/<int:id>", methods=["DELETE"])
def endpoint_get_movie(id: int):

    query = """DELETE FROM experiment
                    WHERE experiment_id = %s ;
                    """

    query_search = """SELECT experiment_id,experiment_date FROM experiment
                    WHERE experiment_id = %s ;"""

    with conn.cursor() as cur:
        cur.execute(query_search, (id,))
        data = list(cur.fetchall())

    if not data:
        return {"error": f"Unable to locate experiment with ID {id}."}, 404

    with conn.cursor() as cur:
        cur.execute(query, (id,))
        conn.commit()

    for experiment in data:
        experiment["experiment_date"] = str(experiment["experiment_date"])

    return data[0], 200


if __name__ == "__main__":
    app.config["DEBUG"] = True
    app.config["TESTING"] = True

    app.run(port=8000, debug=True)

    conn.close()
