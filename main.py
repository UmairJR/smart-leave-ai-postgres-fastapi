from fastapi import FastAPI, Query
import psycopg2
from rapidfuzz import process
import os
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
DB_URL = os.environ["DB_URL"]


def get_db_connection():
    return psycopg2.connect(DB_URL)


# Fetch all employees
def get_all_employees():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT employeeid, name FROM employee_leave_view")
    employees = cursor.fetchall()
    conn.close()

    employee_dict = {}
    for emp_id, name in employees:
        name_lower = name.lower()
        if name_lower in employee_dict:
            employee_dict[name_lower].append(emp_id)
        else:
            employee_dict[name_lower] = [emp_id]

    return employee_dict


# Find closest name match - fuzzzyy
def find_best_matches(input_name, employee_dict):
    match = process.extractOne(input_name.lower(), employee_dict.keys())

    if not match:
        return None, None  # No match found

    best_match, score = match[:2]
    if score < 70:
        return None, None

    return best_match, employee_dict[best_match]


@app.get("/leave-request")
def get_leave_request(employee_name: str = Query(...)):
    employee_dict = get_all_employees()
    best_match, employee_ids = find_best_matches(employee_name, employee_dict)

    if not best_match:
        return {"error": "Employee not found. Check spelling or try again."}

    if len(employee_ids) > 1:
        return {
            "message": f"Multiple employees found for '{best_match}', employee_ids[{employee_ids}]. Please select an Employee ID.",
            "employee_name": best_match,
            "employee_ids": [employee_ids]
        }
    else:
        return {
            "message":f"One employee found = {best_match}",
            "employee_name":best_match,
            "employee_ids":[employee_ids]
        }

@app.get("/leave/{employee_id}")
def get_leave_balance(employee_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT cl_used, total_cl, cl_remaining FROM employee_leave_view WHERE employeeid = %s"
    cursor.execute(query, (employee_id,))
    data = cursor.fetchone()
    conn.close()

    if data:

        return {"remaining_cl": data[2], "total_cl": data[1], "cl_used": data[0]}
    return {"error": "Employee not found"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)
