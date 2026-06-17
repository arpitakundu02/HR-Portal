-- ============================================================
-- backend/schema.sql
-- HR Portal - MySQL Schema Reference
-- ============================================================
-- This file is a reference-only SQL dump of the schema.
-- The actual tables are created via SQLAlchemy (init_db.py).
-- You can run this manually if you prefer raw SQL setup.
-- ============================================================

CREATE DATABASE IF NOT EXISTS hr_portal
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE hr_portal;

-- ============================================================
-- Table: departments
-- ============================================================
CREATE TABLE IF NOT EXISTS departments (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Table: users  (Authentication + Employee Profile)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    employee_id         VARCHAR(50) NOT NULL UNIQUE COMMENT 'e.g. HR-001',
    email               VARCHAR(120) NOT NULL UNIQUE,
    password_hash       VARCHAR(255) NOT NULL,
    role                ENUM('Admin','Employee') NOT NULL DEFAULT 'Employee',
    name                VARCHAR(100) NOT NULL,
    fathers_name        VARCHAR(100),
    dob                 DATE,
    blood_group         VARCHAR(10),
    address             TEXT,
    permanent_address   TEXT,
    current_address     TEXT,
    emergency_contact   VARCHAR(50),
    department_id       INT,
    date_of_joining     DATE,
    salary              DECIMAL(10,2),
    rank                VARCHAR(50),
    aadhar_number       VARCHAR(20),
    resume_url          VARCHAR(255),
    photo_url           VARCHAR(255),
    phone_number        VARCHAR(20),
    manager_id          INT,
    is_line_manager     BOOLEAN NOT NULL DEFAULT FALSE,
    bio                 TEXT,
    experience_summary  TEXT,
    gender              VARCHAR(20) DEFAULT 'Male',
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_dept FOREIGN KEY (department_id)
        REFERENCES departments(id) ON DELETE SET NULL,
    CONSTRAINT fk_user_manager FOREIGN KEY (manager_id)
        REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Table: leave_balances
-- ============================================================
CREATE TABLE IF NOT EXISTS leave_balances (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    employee_id     INT NOT NULL,
    leave_type      ENUM('APL','WFH') NOT NULL,
    allocated       INT NOT NULL DEFAULT 0,
    used            INT NOT NULL DEFAULT 0,
    remaining       INT NOT NULL DEFAULT 0 COMMENT 'May be negative (overdraft allowed)',
    UNIQUE KEY uq_employee_leave_type (employee_id, leave_type),
    CONSTRAINT fk_lb_employee FOREIGN KEY (employee_id)
        REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Table: leaves  (Leave Requests)
-- ============================================================
CREATE TABLE IF NOT EXISTS leaves (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    employee_id     INT NOT NULL,
    leave_type      ENUM('APL','WFH') NOT NULL,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    reason          TEXT,
    status          ENUM('Pending','Approved','Rejected') NOT NULL DEFAULT 'Pending',
    actioned_by     INT COMMENT 'Admin user id who actioned the request',
    actioned_at     DATETIME,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_leave_employee FOREIGN KEY (employee_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_leave_actioned_by FOREIGN KEY (actioned_by)
        REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Table: attendance
-- ============================================================
CREATE TABLE IF NOT EXISTS attendance (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    employee_id     INT NOT NULL,
    date            DATE NOT NULL,
    check_in        DATETIME,
    check_out       DATETIME,
    working_hours   DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    latitude        DOUBLE COMMENT 'Check-in GPS latitude',
    longitude       DOUBLE COMMENT 'Check-in GPS longitude',
    UNIQUE KEY uq_employee_date (employee_id, date),
    CONSTRAINT fk_att_employee FOREIGN KEY (employee_id)
        REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Table: meetings
-- ============================================================
CREATE TABLE IF NOT EXISTS meetings (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    title               VARCHAR(150) NOT NULL,
    description         TEXT,
    department_id       INT COMMENT 'NULL = company-wide meeting',
    scheduled_at        DATETIME NOT NULL,
    duration_minutes    INT NOT NULL DEFAULT 30,
    link                VARCHAR(255),
    created_by          INT NOT NULL,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_meeting_dept FOREIGN KEY (department_id)
        REFERENCES departments(id) ON DELETE SET NULL,
    CONSTRAINT fk_meeting_creator FOREIGN KEY (created_by)
        REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Table: tasks
-- ============================================================
CREATE TABLE IF NOT EXISTS tasks (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(150) NOT NULL,
    description     TEXT,
    employee_id     INT NOT NULL,
    status          ENUM('Pending','In Progress','Completed') NOT NULL DEFAULT 'Pending',
    due_date        DATE,
    assigned_by     INT NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_task_employee FOREIGN KEY (employee_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_task_assigner FOREIGN KEY (assigned_by)
        REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Default Departments Seed
-- ============================================================
INSERT IGNORE INTO departments (name, description) VALUES
    ('Research',       'Research and Innovation Department'),
    ('Tech',           'Technology and Engineering Department'),
    ('GIS',            'Geographic Information Systems Department'),
    ('Data Scientist', 'Data Science and Analytics Department'),
    ('Broker',         'Brokerage Services Department'),
    ('Execution',      'Operations and Execution Department'),
    ('Account',        'Accounts and Finance Department'),
    ('Management',     'Senior Management Department');
