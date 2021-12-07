CREATE TABLE Patient(
    username VARCHAR(100),
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (username)
);

CREATE TABLE Caregiver(
    username VARCHAR(100),
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (username)
);

CREATE TABLE Availabilities(
    time date,
    username varchar(100) REFERENCES Caregiver,
    PRIMARY KEY (time, username)
);

CREATE TABLE Vaccines(
    name varchar(100),
    doses int,
    PRIMARY KEY (name)
);


CREATE TABLE Appointment(
    aid INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
    p_username VARCHAR(100),
    c_username VARCHAR(100),
    v_name VARCHAR(100),
    time date,
    FOREIGN KEY (time) REFERENCES Availabilities(time),
    FOREIGN KEY (p_username) REFERENCES Patient(username),
    FOREIGN KEY (c_username) REFERENCES Caregiver(username),
    FOREIGN KEY (v_name) REFERENCES Vaccines(name),
);