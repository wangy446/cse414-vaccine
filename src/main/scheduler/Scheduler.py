import sys
from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import datetime

'''
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
'''
current_patient = None

current_caregiver = None

def check_password(tokens):
    if len(tokens) != 3:
        print("Please try again!")
        return

    password = tokens[2]
    if len(password) < 8:
        print('Please enter at least 8 characters')
        return

    count_up = 0
    count_low = 0
    count_digit = 0
    count_special = 0

    for char in password:
        if char.isupper():
            count_up += 1
        elif char.islower():
            count_low += 1
        elif char.isdigit():
            count_digit += 1
        elif char == '@' or char == '!' or char == '#' or char == '?':
            count_special += 1

    if count_up == 0:
        print("Please include at least 1 uppercase character")
        return
    elif count_low == 0:
        print('Please include at least 1 lowercase character')
        return
    elif count_digit == 0:
        print('Please include at lease 1 digit')
        return
    elif count_special == 0:
        print('Please include one of the special character(@, !, #, ?)')
        return

def create_patient(tokens):  # TODO
    if len(tokens) != 3:
        print("Please try again!")
        return
    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_patient(username):
        print("Username taken, try again!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    try:
        patient = Patient(username, salt=salt, hash=hash)
        # save to caregiver information to our database
        patient.save_to_db()
        print(" *** Account created successfully *** ")
    except pymssql.Error:
        print("Create failed")
        return


def username_exists_patient(username):  # TODO
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Patient WHERE username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['username'] is None
    except pymssql.Error:
        print("Error occurred when checking username")
        cm.close_connection()
    cm.close_connection()
    return False


def create_caregiver(tokens):
    # create_caregiver <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_caregiver(username):
        print("Username taken, try again!")
        return

    if len(password) < 8:
        print('Please enter at least 8 characters')
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver
    try:
        caregiver = Caregiver(username, salt=salt, hash=hash)
        # save to caregiver information to our database
        try:
            caregiver.save_to_db()
        except:
            print("Create failed, Cannot save")
            return
        print(" *** Account created successfully *** ")
    except pymssql.Error:
        print("Create failed")
        return


def username_exists_caregiver(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Caregiver WHERE username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['username'] is not None
    except pymssql.Error:
        print("Error occurred when checking username")
        cm.close_connection()
    cm.close_connection()
    return False


def login_patient(tokens):  # TODO
    global current_patient
    if current_patient is not None or current_caregiver is not None:
        print("Already logged-in!")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        patient = Patient(username, password=password).get()
    except pymssql.Error:
        print("Error occurred when logging in")

    # check if the login was successful
    if Patient is None:
        print("Please try again!")
    else:
        print("Patient logged in as: " + username)
        current_patient = patient


def login_caregiver(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("Already logged-in!")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        try:
            caregiver = Caregiver(username, password=password).get()
        except:
            print("Get Failed")
            return
    except pymssql.Error:
        print("Error occurred when logging in")

    # check if the login was successful
    if caregiver is None:
        print("Please try again!")
    else:
        print("Caregiver logged in as: " + username)
        current_caregiver = caregiver


# what does global means?
# what is token
# do I need to change tokens to date?
def search_caregiver_schedule(tokens):  # TODO
    global current_caregiver
    global current_patient
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return

    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])

    if current_caregiver is not None and current_patient is None:
        try:
            d = datetime.datetime(year, month, day)
            d_str = str(d)
            d_final = d_str[:10]
            try:
                current_caregiver.check_availability(d_final)
            except:
                print("Search Availability Failed")
                return
        except ValueError:
            print("Please enter a valid date!")
        except pymssql.Error as db_err:
            print("Error occurred when checking availability")
    elif current_caregiver is None and current_patient is not None:
        try:
            d = datetime.datetime(year, month, day)
            d_str = str(d)
            d_final = d_str[:10]
            # how to check availability based on time?

            try:
                current_patient.check_availability(d_final)
            except:
                print("Search Availability Failed")
        except ValueError:
            print("Please enter a valid date!")
        except pymssql.Error as db_err:
            print("Error occurred when checking availability")



def reserve(tokens): # TODO #不会
    global current_patient
    if current_patient is None:
        print("Please login as a patient first!")
        return

    if len(tokens) != 3:
        print("Please try again!")
        return

    date = tokens[1]
    vaccine_name = tokens[2]

    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day)
        d_str = str(d)
        d_final = d_str[:10]
        try:
            caregiver = current_patient.reserve_availability(d_final)
            if caregiver is None:
                print('No Available Caregiver')
                return
            try:
                current_patient.decrease_doses(vaccine_name, 1)
                try:
                    current_patient.delete_availability(caregiver, d_final)
                    try:
                        current_patient.make_appointment(caregiver, d_final, vaccine_name)
                    except:
                        print('Make Appointment Failed')
                        return
                except:
                    print("Choose Availability Failed")
                    return
            except:
                print('Choose Vaccine Failed')
                return
        except:
            print("Choose Availability Failed")
            return
    except ValueError:
        print("Please enter a valid date!")
    except pymssql.Error as db_err:
        print("Error occurred when making reservation")


def upload_availability(tokens):
    #  upload_availability <date>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day)
        try:
            current_caregiver.upload_availability(d)
        except:
            print("Upload Availability Failed")
        print("Availability uploaded!")
    except ValueError:
        print("Please enter a valid date!")
    except pymssql.Error as db_err:
        print("Error occurred when uploading availability")


def cancel(tokens):
    global current_patient
    global current_caregiver
    if current_patient is None and current_caregiver is None:
        print("Please login in first!")
        return

    if len(tokens) != 2:
        print("Please try again!")
        return

    id = int(tokens[1])

    if current_patient is None and current_caregiver is not None:
        try:
            appoint_info = current_caregiver.find_appoint(id)
            vaccine = appoint_info[3]
            date = str(appoint_info[4])
            date_tokens = date.split("-")
            month = int(date_tokens[1])
            day = int(date_tokens[2])
            year = int(date_tokens[0])
            d = datetime.datetime(year, month, day)
            d_str = str(d)
            d_final = d_str[:10]
            try:
                current_caregiver.increase_doses(vaccine, 1)
                try:
                    current_caregiver.upload_availability(d_final)
                    try:
                        current_caregiver.cancel_appointment(id)
                    except:
                        print('Cancel Appointment Failed')
                        return
                except:
                    print('Restore Appointment Failed')
                    return
            except:
                print('Upload Vaccine Failed')
                return
        except ValueError:
            print("Please enter a Valid Appointment Id!")
        except pymssql.Error as db_err:
            print("Error occurred when making reservation")
    elif current_patient is not None and current_caregiver is None:
        if current_patient is None and current_caregiver is not None:
            try:
                appoint_info = current_patient.find_appoint(id)
                vaccine = appoint_info[3]
                date = str(appoint_info[4])
                date_tokens = date.split("-")
                month = int(date_tokens[1])
                day = int(date_tokens[2])
                year = int(date_tokens[0])
                d = datetime.datetime(year, month, day)
                d_str = str(d)
                d_final = d_str[:10]
                try:
                    current_patient.increase_doses(vaccine, 1)
                    try:
                        current_patient.upload_availability(d_final)
                        try:
                            current_patient.cancel_appointment(id)
                        except:
                            print('Cancel Appointment Failed')
                            return
                    except:
                        print('Restore Appointment Failed')
                        return
                except:
                    print('Upload Vaccine Failed')
                    return
            except ValueError:
                print("Please enter a Valid Appointment Id!")
            except pymssql.Error as db_err:
                print("Error occurred when making reservation")


def add_doses(tokens):
    #  add_doses <vaccine> <number>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    #  check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine_name = tokens[1]
    doses = int(tokens[2])
    vaccine = None
    try:
        try:
            vaccine = Vaccine(vaccine_name, doses).get()
        except:
            print("Failed to get Vaccine!")
            return
    except pymssql.Error:
        print("Error occurred when adding doses")

    # check 3: if getter returns null, it means that we need to create the vaccine and insert it into the Vaccines
    #          table

    if vaccine is None:
        try:
            vaccine = Vaccine(vaccine_name, doses)
            try:
                vaccine.save_to_db()
            except:
                print("Failed To Save")
                return
        except pymssql.Error:
            print("Error occurred when adding doses")
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            try:
                vaccine.increase_available_doses(doses)
            except:
                print("Failed to increase available doses!")
                return
        except pymssql.Error:
            print("Error occurred when adding doses")

    print("Doses updated!")


def show_appointments(tokens):  # TODO
    global current_caregiver
    global current_patient
    if current_caregiver is None and current_patient is None:
        print('Please log in first!')

    if current_caregiver is not None and current_patient is None:
        try:
            current_caregiver.show_availability()
        except pymssql.Error:
            print("Error occurred when showing appointment")
    elif current_caregiver is None and current_patient is not None:
        try:
            current_patient.show_availability()
        except pymssql.Error:
            print("Error occurred when showing appointment")


def logout(tokens):
    global current_patient
    global current_caregiver

    if current_patient is None and current_caregiver is None:
        print("Please log in first!")
        return

    if current_patient is not None and current_caregiver is None:
        try:
            current_patient = None
            print('Log out successfully')
        except pymssql.Error:
            print("Error occurred when logging out")
    elif current_patient is None and current_caregiver is not None:
        try:
            current_caregiver = None
            print('Log out successfully')
        except pymssql.Error:
            print("Error occurred when logging out")


def start():
    stop = False
    while not stop:
        print()
        print(" *** Please enter one of the following commands *** ")
        print("> create_patient <username> <password>")  # //TODO: implement create_patient (Part 1)
        print("> create_caregiver <username> <password>")
        print("> login_patient <username> <password>")  # // TODO: implement login_patient (Part 1)
        print("> login_caregiver <username> <password>")
        print("> search_caregiver_schedule <date>")  # // TODO: implement search_caregiver_schedule (Part 2)
        print("> reserve <date> <vaccine>")  # // TODO: implement reserve (Part 2)
        print("> upload_availability <date>")
        print("> cancel <appointment_id>")  # // TODO: implement cancel (extra credit)
        print("> add_doses <vaccine> <number>")
        print("> show_appointments")  # // TODO: implement show_appointments (Part 2)
        print("> logout")  # // TODO: implement logout (Part 2)
        print("> Quit")
        print()
        response = ""
        print("> Enter: ", end='')

        try:
            response = str(input())
        except ValueError:
            print("Type in a valid argument")
            break

        test_tokens = response.split(" ")
        response = response.lower()
        tokens = response.split(" ")
        if len(tokens) == 0:
            ValueError("Try Again")
            continue
        operation = tokens[0]
        if operation == "create_patient":
            check_password(test_tokens)
            create_patient(tokens)
        elif operation == "create_caregiver":
            check_password(test_tokens)
            create_caregiver(tokens)
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(tokens)
        elif operation == "reserve":
            reserve(tokens)
        elif operation == "upload_availability":
            upload_availability(tokens)
        elif operation == 'cancel':
            cancel(tokens)
        elif operation == "add_doses":
            add_doses(tokens)
        elif operation == "show_appointments":
            show_appointments(tokens)
        elif operation == "logout":
            logout(tokens)
        elif operation == "quit":
            print("Thank you for using the scheduler, Goodbye!")
            stop = True
        else:
            print("Invalid Argument")


if __name__ == "__main__":
    '''
    // pre-define the three types of authorized vaccines
    // note: it's a poor practice to hard-code these values, but we will do this ]
    // for the simplicity of this assignment
    // and then construct a map of vaccineName -> vaccineObject
    '''

    # start command line
    print()
    print("Welcome to the COVID-19 Vaccine Reservation Scheduling Application!")

    start()
