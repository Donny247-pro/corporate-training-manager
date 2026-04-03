import os
import csv
import math
import sqlite3
DB_PATH = "db/corporate.db"

def init_db():
    os.makedirs("db", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    with open("db/schema.sql") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

def read_students(file_path):
    students = []
    with open(file_path, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 4:
                continue  # skip bad rows
            students.append({
                "first_name": row[0],
                "last_name": row[1],
                "email": row[2],
                "employee_id": row[3]
            })
    return students

def read_courses(file_path):
    with open(file_path) as f:
        return [line.strip() for line in f if line.strip()]

def create_sections(students, course_name, max_size=35):
    num_sections = math.ceil(len(students) / max_size)
    sections = []
    for i in range(num_sections):
        start = i * max_size
        end = start + max_size
        sections.append({
            "section_name": f"{course_name} - Section {i+1}",
            "students": students[start:end]
        })
    return sections

def load_to_db(students, courses, cohort_name=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Get cohort_id from name
    cur.execute("SELECT cohort_id FROM Cohort WHERE cohort_name = ?", (cohort_name,))
    cohort_id_row = cur.fetchone()
    if not cohort_id_row:
        raise ValueError("Cohort not found")
    cohort_id = cohort_id_row[0]

    # Insert new courses if provided
    for c in courses:
        cur.execute("INSERT OR IGNORE INTO Course (course_name) VALUES (?)", (c,))
    conn.commit()

    # Always fetch course IDs
    cur.execute("SELECT course_name, course_id FROM Course")
    course_ids = {name: cid for name, cid in cur.fetchall()}

    # Insert students
    student_ids = {}
    for s in students:
        cur.execute("""
            INSERT OR IGNORE INTO Student (employee_id, first_name, last_name, email)
            VALUES (?, ?, ?, ?)
        """, (s['employee_id'], s['first_name'], s['last_name'], s['email']))
        cur.execute("SELECT student_id FROM Student WHERE employee_id=?", (s['employee_id'],))
        student_ids[s['employee_id']] = cur.fetchone()[0]

    # Create sections and enroll students
    for course_name, course_id in course_ids.items():
        sections = create_sections(students, course_name)
        for i, sec in enumerate(sections, start=1):
            section_name = f"{course_name} - Section {i}"
            cur.execute("""
                INSERT INTO Section (course_id, cohort_id, section_number, section_name)
                VALUES (?, ?, ?, ?)
            """, (course_id, cohort_id, i, section_name))
            section_id = cur.lastrowid

            for s in sec['students']:
                cur.execute("""
                    INSERT INTO Enrollment (student_id, section_id)
                    VALUES (?, ?)
                """, (student_ids[s['employee_id']], section_id))

    conn.commit()
    conn.close()


def get_section_report(cohort_name=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT Course.course_name, Section.section_number, COUNT(Enrollment.student_id)
        FROM Section
        JOIN Course ON Section.course_id = Course.course_id
        JOIN Cohort ON Section.cohort_id = Cohort.cohort_id
        LEFT JOIN Enrollment ON Section.section_id = Enrollment.section_id
        WHERE Cohort.cohort_name = ?
        GROUP BY Section.section_id
        ORDER BY Course.course_name, Section.section_number
    """, (cohort_name,))
    rows = cur.fetchall()
    conn.close()

    grouped = {}
    for course, section_num, count in rows:
        grouped.setdefault(course, []).append({
            "section_number": section_num,
            "num_students": count
        })
    return grouped

def get_student_report(cohort_name=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT Course.course_name, Section.section_number,
               Student.first_name || ' ' || Student.last_name AS student_name,
               Student.email, Student.employee_id
        FROM Enrollment
        JOIN Section ON Enrollment.section_id = Section.section_id
        JOIN Course ON Section.course_id = Course.course_id
        JOIN Student ON Enrollment.student_id = Student.student_id
        JOIN Cohort ON Section.cohort_id = Cohort.cohort_id
        WHERE Cohort.cohort_name = ?
        ORDER BY Course.course_name, Section.section_number
    """, (cohort_name,))
    rows = cur.fetchall()
    conn.close()

    grouped = {}
    for course, section_num, name, email, emp_id in rows:
        grouped.setdefault(course, []).append({
            "section_number": section_num,
            "student_name": name,
            "email": email,
            "employee_id": emp_id
        })
    return grouped
