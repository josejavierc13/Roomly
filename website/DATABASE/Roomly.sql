/* This is the database schema for Roomly, a student home 
booking application. */

/* This table represents the account information for each user */
CREATE TABLE ACCOUNT (
    account_id_pk int PRIMARY KEY,
    email varchar(255) UNIQUE NOT NULL,
    hashed_password varchar(255) NOT NULL,
    first_name varchar(255) NOT NULL,
    last_name varchar(255) NOT NULL,
    phone_number varchar(20),
    profile_picture varchar(255),
    date_created timestamp DEFAULT CURRENT_TIMESTAMP,
    account_status varchar(20) CHECK (account_status IN ('active', 'inactive', 'suspended')) NOT NULL,
    account_type varchar(20) CHECK (account_type IN ('OWNER', 'STUDENT')) NOT NULL DEFAULT 'STUDENT'
);

/* This table represents the amenities listed on Roomly */
CREATE TABLE AMENITIES (
    amenity_id_pk int PRIMARY KEY,
    name varchar(255) NOT NULL
);

/* This table represents the universities that are listed on Roomly */
CREATE TABLE UNIVERSITY (
    university_id_pk int PRIMARY KEY,
    name varchar(255) UNIQUE NOT NULL,
    city varchar(255) NOT NULL,
    state varchar(255) NOT NULL,
    country varchar(255) NOT NULL,
    website varchar(255) NOT NULL,
    latitude decimal(10, 7) NOT NULL,
    longitude decimal(10, 7) NOT NULL
);

/* This table represents the accounts that are students listed on Roomly */
CREATE TABLE STUDENT (
    student_id_pk int PRIMARY KEY,
    major varchar(255) NOT NULL CHECK (major IN ('Computer Science', 'Engineering', 'Business', 'Biology', 'Psychology', 'Other')),
    year_of_study int NOT NULL,
    bio VARCHAR(255),
    budget_min float,
    budget_max float,
    smoking_preference BOOLEAN,
    pets_preference BOOLEAN,
    sleep_schedule_preference TIME,
    student_active_status boolean,
    university_id_fk int,
    account_id_fk int NOT NULL,
    FOREIGN KEY (university_id_fk) REFERENCES UNIVERSITY(university_id_pk), -- This is a foreign key that references the UNIVERSITY table
    FOREIGN KEY (account_id_fk) REFERENCES ACCOUNT(account_id_pk) -- This is a foreign key that references the ACCOUNT table
);

/* This table represents the accounts that are owners listed on Roomly */
CREATE TABLE OWNER (
    owner_id_pk int PRIMARY KEY,
    company_name varchar(255),
    verified_status boolean,
    rating_average FLOAT DEFAULT 0 CHECK (rating_average >= 0 AND rating_average <= 5),
    account_id_fk int NOT NULL,
    FOREIGN KEY (account_id_fk) REFERENCES ACCOUNT(account_id_pk) -- This is a foreign key that references the ACCOUNT table
);

/* This table represents the accounts that are admins listed on Roomly */
CREATE TABLE ADMIN (
    admin_id_pk int PRIMARY KEY,
    role_level varchar(255) CHECK (role_level IN ('superadmin', 'moderator', 'support')) NOT NULL,
    account_id_fk int NOT NULL,
    FOREIGN KEY (account_id_fk) REFERENCES ACCOUNT(account_id_pk) -- This is a foreign key that references the ACCOUNT table
);

/* This table represents the properties listed on Roomly */
CREATE TABLE PROPERTY (
    property_id_pk int PRIMARY KEY,
    title varchar(255) NOT NULL,
    description text NOT NULL,
    address varchar(255) NOT NULL,
    city varchar(255) NOT NULL,
    state varchar(255) NOT NULL,
    country varchar(255) NOT NULL,
    postal_code VARCHAR(10) NOT NULL,
    price_per_month float CHECK (price_per_month > 0) NOT NULL,
    deposit_amount float NOT NULL,
    number_of_bedrooms int NOT NULL,
    number_of_bathrooms int NOT NULL DEFAULT 1,
    sqr_ft int NOT NULL,
    amenities text,
    availability_status boolean NOT NULL,
    date_posted timestamp DEFAULT CURRENT_TIMESTAMP,
    owner_id_fk int NOT NULL,
    university_id_fk int,
    FOREIGN KEY (owner_id_fk) REFERENCES OWNER(owner_id_pk), -- This is a foreign key that references the OWNER table
    FOREIGN KEY (university_id_fk) REFERENCES UNIVERSITY(university_id_pk) -- This is a foreign key that references the UNIVERSITY table
);

/* This table represents the reviews left by students for properties listed on Roomly */
CREATE TABLE REVIEW_PROPERTY (
    review_property_id_pk int PRIMARY KEY,
    rating int NOT NULL,
    comment text,
    date_posted timestamp DEFAULT CURRENT_TIMESTAMP,
    student_id_fk int UNIQUE NOT NULL,
    property_id_fk int UNIQUE NOT NULL,
    FOREIGN KEY (student_id_fk) REFERENCES STUDENT(student_id_pk), -- This is a foreign key that references the STUDENT table
    FOREIGN KEY (property_id_fk) REFERENCES PROPERTY(property_id_pk) -- This is a foreign key that references the PROPERTY table
);

/* This table represents the amenities that are associated with each property listed on Roomly with PK_FK */
CREATE TABLE PROPERTY_AMENITY (
    property_id_pk_fk int,
    amenity_id_pk_fk int,
    PRIMARY KEY (property_id_pk_fk, amenity_id_pk_fk),
    FOREIGN KEY (property_id_pk_fk) REFERENCES PROPERTY(property_id_pk), -- This is a foreign key that references the PROPERTY table
    FOREIGN KEY (amenity_id_pk_fk) REFERENCES AMENITIES(amenity_id_pk) -- This is a foreign key that references the AMENITIES table
);

/* This table represents the bookings made by students for properties listed on Roomly */
CREATE TABLE BOOKING (
    booking_id_pk int PRIMARY KEY,
    start_date date NOT NULL,
    end_date date NOT NULL,
    total_price float NOT NULL,
    booking_status varchar(20) CHECK (booking_status IN ('pending', 'confirmed', 'cancelled')) NOT NULL,
    student_id_fk int NOT NULL,
    property_id_fk int NOT NULL,
    FOREIGN KEY (student_id_fk) REFERENCES STUDENT(student_id_pk), -- This is a foreign key that references the STUDENT table
    FOREIGN KEY (property_id_fk) REFERENCES PROPERTY(property_id_pk) -- This is a foreign key that references the PROPERTY table
);

CREATE TABLE PROPERTY_IMAGES (
    image_id_pk int PRIMARY KEY,
    image_url varchar(255) NOT NULL,
    property_id_fk int NOT NULL,
    FOREIGN KEY (property_id_fk) REFERENCES PROPERTY(property_id_pk) -- This is a foreign key that references the PROPERTY table
);

CREATE TABLE PROPERTY_VIDEOS (
    video_id_pk int PRIMARY KEY,
    video_url varchar(255) NOT NULL,
    property_id_fk int NOT NULL,
    FOREIGN KEY (property_id_fk) REFERENCES PROPERTY(property_id_pk) -- This is a foreign key that references the PROPERTY table
);

CREATE TABLE PROPERTY_BOOKING (
    booking_id_pk int PRIMARY KEY,
    student_id_fk int NOT NULL,
    property_id_fk int NOT NULL,
    booking_date timestamp DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id_fk) REFERENCES STUDENT(student_id_pk), -- This is a foreign key that references the STUDENT table
    FOREIGN KEY (property_id_fk) REFERENCES PROPERTY(property_id_pk) -- This is a foreign key that references the PROPERTY table
);


/* Sample seed data for quick integration testing */

