import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

# Import your processing functions
from utils.processing import (
    DB_PATH,
    init_db,           # <-- add this
    load_to_db,
    read_students,
    read_courses,
    get_section_report,
    get_student_report
)

app = Flask(__name__, template_folder="templates ")
app.config["UPLOAD_FOLDER"] = "data"

# Make sure folders exist
os.makedirs("data", exist_ok=True)
os.makedirs("db", exist_ok=True)

# Initialize DB schema (safe with IF NOT EXISTS in schema.sql)
init_db()


@app.route("/")
def index():
    return render_template("home.html")


@app.route("/add_company")
def add_company():
    return render_template("add_company.html")


@app.route("/create_program")
def create_program():
    return render_template("create_program.html")


# -------------------------
# ENROLL STUDENTS (Upload CSV + TXT)
# -------------------------
@app.route("/enroll_students", methods=["GET", "POST"])
def enroll_students():
    cohorts = get_all_cohorts()
    if request.method == "POST":
        cohort = request.form.get("cohort")
        student_file = request.files.get("student_file")

        if not cohort:
            return "Please select a cohort.", 400

        if student_file:
            student_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{cohort}_students.csv")
            student_file.save(student_path)

            students = read_students(student_path)
            load_to_db(students, [], cohort_name=cohort)
            return redirect(url_for("index"))

    return render_template("enroll_students.html", cohorts=cohorts)


def get_all_cohorts():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT cohort_name FROM Cohort ORDER BY cohort_id")
    cohorts = [row[0] for row in cur.fetchall()]
    conn.close()
    return cohorts

# -------------------------
# ADD COURSE
# -------------------------
@app.route("/add_course", methods=["GET", "POST"])
@app.route("/add_courses", methods=["GET", "POST"])
def add_course():
    cohorts = get_all_cohorts()
    if request.method == "POST":
        cohort = request.form.get("cohort")
        course_file = request.files.get("course_file")

        if not cohort:
            return "Please select a cohort.", 400

        if course_file:
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{cohort}_new_course.txt")
            course_file.save(file_path)

            courses = read_courses(file_path)
            load_to_db([], courses, cohort_name=cohort)
            return redirect(url_for("index"))

    return render_template("add_courses.html", cohorts=cohorts)



# -------------------------
# SECTION REPORT PER COHORT
# -------------------------
@app.route("/report_sections")
@app.route("/section_summary_report")
def report_sections():
    cohort = request.args.get("cohort")
    report = get_section_report(cohort_name=cohort)
    cohorts = get_all_cohorts()
    return render_template("report_sections.html", report=report, cohorts=cohorts)



@app.route("/manage_cohorts", methods=["GET", "POST"])
def manage_cohorts():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Add new cohort if POST
    if request.method == "POST":
        cohort_name = request.form.get("cohort_name").strip()
        if cohort_name:
            cur.execute("INSERT OR IGNORE INTO Cohort (cohort_name) VALUES (?)", (cohort_name,))
            conn.commit()

    # Fetch all cohorts to display
    cur.execute("SELECT cohort_id, cohort_name FROM Cohort ORDER BY cohort_id")
    cohorts = cur.fetchall()
    conn.close()

    return render_template("manage_cohorts.html", cohorts=cohorts)




# -------------------------
# STUDENT ENROLLMENT REPORT PER COHORT
# -------------------------
@app.route("/report_students")
@app.route("/student_roster")
def report_students():
    cohort = request.args.get("cohort")
    report = get_student_report(cohort_name=cohort)
    cohorts = get_all_cohorts()
    return render_template("report_students.html", report=report, cohorts=cohorts)


if __name__ == "__main__":
    app.run(debug=True)
