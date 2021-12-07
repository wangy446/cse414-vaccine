import sys
sys.path.append("../util/*")
sys.path.append("../db/*")
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql

class Patient:
    def __init__(self, username, password=None, salt=None, hash=None):
        self.username = username
        self.password = password
        self.salt = salt
        self.hash = hash

    # getters
    def get(self):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor(as_dict=True)

        get_patient_details = "SELECT Salt, Hash FROM Patient WHERE username = %s"
        try:
            cursor.execute(get_patient_details, self.username)
            for row in cursor:
                curr_salt = row['Salt']
                curr_hash = row['Hash']
                calculated_hash = Util.generate_hash(self.password, curr_salt)
                # how to say something to remind the user about wrong password?
                if not curr_hash == calculated_hash:
                    cm.close_connection()
                    return None
                else:
                    self.salt = curr_salt
                    self.hash = calculated_hash
                    return self
        except pymssql.Error:
            print("Error occurred when getting Patient")
            cm.close_connection()

        cm.close_connection()
        return None

    def get_username(self):
        return self.username

    def get_salt(self):
        return self.salt

    def get_hash(self):
        return self.hash

    def save_to_db(self):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()

        create_patient = "INSERT INTO Patient VALUES (%s, %s, %s)"
        try:
            cursor.execute(create_patient, (self.username, self.salt, self.hash))
            # you must call commit() to persist your data if you don't set autocommit to True
            conn.commit()
        except pymssql.Error as db_err:
            print("Error occurred when inserting Patient")
            sqlrc = str(db_err.args[0])
            print("Exception code: " + str(sqlrc))
            cm.close_connection()
        cm.close_connection()

    def check_availability(self, d):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor(as_dict=True)

        # something is wrong at here
        check_avail = "SELECT DISTINCT a.username as username, v.name as name, v.doses as dose " \
                      "FROM Availabilities a, Vaccines v WHERE a.time = %s"
        try:
            cursor.execute(check_avail, d)
            for row in cursor:
                curr_caregiver = row['username']
                v_name = row['name']
                v_dose = row['dose']
                print('Available schedule:', curr_caregiver)
                print('Available vaccine:', v_name)
                print('Available dose:', v_dose)
                # self.username = curr_caregiver
                # return self
            conn.commit()
        except pymssql.Error:
            print("Error occurred when checking caregiver availability")
            cm.close_connection()
        cm.close_connection()

# 不确定怎么做
    def reserve_availability(self, d):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor(as_dict=True)

        select_availability = "SELECT TOP 1 username FROM Availabilities WHERE time = %s"
        try:
            cursor.execute(select_availability, d)
            for row in cursor:
                curr_caregiver = row['username']
                return curr_caregiver
        # you must call commit() to persist your data if you don't set autocommit to True
        # conn.commit()
        except pymssql.Error:
            print("Error occurred when updating caregiver availability")
            cm.close_connection()
        cm.close_connection()

    def make_appointment(self, c_username, d, v_name):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor(as_dict=True)

        # how to randomly assign a caregiver
        make_appointment = "INSERT INTO Appointment (p_username, c_username, v_name, time) VALUES (%s, %s, %s, %s)"
        show_appointment = 'SELECT aid, c_username FROM Appointment WHERE p_username = %s'
        try:
            cursor.execute(make_appointment, (self.username, c_username, v_name, d))
            # you must call commit() to persist your data if you don't set autocommit to True
            conn.commit()
            try:
                cursor.execute(show_appointment, self.username)
                for row in cursor:
                    aid = row['aid']
                    c_name = row['c_username']
                    print('Appointment with:', c_name, 'ID:', aid)
            except pymssql.Error:
                print("Error occurred when selecting availability")
                cm.close_connection()
        except pymssql.Error:
            print("Error occurred when updating caregiver availability")
            cm.close_connection()
        cm.close_connection()

    def delete_availability(self, c_username, d):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()

        delete_availability = "DELETE FROM Availabilities WHERE username = %s AND time = %s"
        try:
            cursor.execute(delete_availability, (c_username, d))
            # you must call commit() to persist your data if you don't set autocommit to True
            conn.commit()
        except pymssql.Error:
            print("Error occurred when deleting caregiver availability")
            cm.close_connection()
        cm.close_connection()

    def decrease_doses(self, vaccine_name, num):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor(as_dict=True)

        vaccine_avail = 'SELECT doses FROM Vaccines WHERE name = %s'
        update_vaccine_availability = "UPDATE Vaccines SET doses = %d WHERE name = %s"
        try:
            cursor.execute(vaccine_avail, vaccine_name)
            for row in cursor:
                dose_num = int(row['doses'])
                if dose_num - num < 0:
                    ValueError("Not enough available doses!")
                else:
                    dose_num -= num
            try:
                cursor.execute(update_vaccine_availability, (dose_num, vaccine_name))
                # you must call commit() to persist your data if you don't set autocommit to True
                conn.commit()
            except pymssql.Error:
                print("Error occurred when updating vaccine availability")
                cm.close_connection()
        except pymssql.Error:
            print("Error occurred when decrease doses")
            cm.close_connection()
        cm.close_connection()

    def show_availability(self):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor(as_dict=True)

        show_availability = "SELECT aid, c_username, v_name, time FROM Appointment WHERE p_username = %s"
        try:
            cursor.execute(show_availability, self.username)
            for row in cursor:
                aid = row['aid']
                c_username = row['c_username']
                v_name = row['v_name']
                time = row['time']
                print('Appointment ID:', aid, 'Caregiver Name:', c_username, 'Time:', time, 'Vaccine name:', v_name)
            conn.commit()
        except pymssql.Error:
            print("Error occurred when showing appointment")
            cm.close_connection()
        cm.close_connection()

    def find_appoint(self, id):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor(as_dict=True)

        find_appointment = "SELECT * FROM Appointment WHERE aid = %s"
        try:
            cursor.execute(find_appointment, id)
            for row in cursor:
                aid = row['aid']
                p_username = row['p_username']
                c_username = row['c_username']
                v_name = row['v_name']
                date = row['time']
                return aid, p_username, c_username, v_name, date
            conn.commit()
        except pymssql.Error:
            print("Error occurred when find appointment")
            cm.close_connection()
        cm.close_connection()

    def increase_doses(self, vaccine_name, num):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor(as_dict=True)

        vaccine_avail = 'SELECT doses FROM Vaccines WHERE name = %s'
        update_vaccine_availability = "UPDATE Vaccines SET doses = %d WHERE name = %s"
        try:
            cursor.execute(vaccine_avail, vaccine_name)
            for row in cursor:
                dose_num = int(row['doses'])
                dose_num += num
            try:
                cursor.execute(update_vaccine_availability, (dose_num, vaccine_name))
                # you must call commit() to persist your data if you don't set autocommit to True
                conn.commit()
            except pymssql.Error:
                print("Error occurred when updating vaccine availability")
                cm.close_connection()
        except pymssql.Error:
            print("Error occurred when decrease doses")
            cm.close_connection()
        cm.close_connection()

    def cancel_appointment(self, id):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor(as_dict=True)

        # how to randomly assign a caregiver
        make_appointment = "DELETE FROM Appointment WHERE aid = %s"
        try:
            cursor.execute(make_appointment, id)
            print('Cancel Appointment Successful!')
            # you must call commit() to persist your data if you don't set autocommit to True
            conn.commit()
        except pymssql.Error:
            print("Error occurred when updating caregiver availability")
            cm.close_connection()
        cm.close_connection()


