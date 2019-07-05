-- Initialize the database.
-- Drop any existing data and create empty tables and view.

DROP TABLE IF EXISTS employee;
DROP TABLE IF EXISTS department;
DROP TABLE IF EXISTS record;
DROP VIEW IF EXISTS statistics;

CREATE TABLE employee (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  type BOOLEAN NOT NULL DEFAULT 0,
  realname TEXT NOT NULL,
  dept_id INTEGER NOT NULL,
  permission TEXT NOT NULL DEFAULT '',
  FOREIGN KEY (dept_id) REFERENCES department (id)
);

CREATE TABLE department (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dept_name TEXT UNIQUE NOT NULL
);

CREATE TABLE record (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dept_id INTEGER NOT NULL,
  type BOOLEAN NOT NULL,
  empl_id INTEGER NOT NULL,
  date DATE NOT NULL,
  duration INTEGER NOT NULL,
  describe TEXT NOT NULL DEFAULT '',
  status INTEGER NOT NULL DEFAULT 0,
  created TIMESTAMP NOT NULL DEFAULT (datetime('now', 'localtime')),
  createdby TEXT,
  verifiedby TEXT,
  FOREIGN KEY (empl_id) REFERENCES employee (id),
  FOREIGN KEY (dept_id) REFERENCES department (id)
);

CREATE VIEW statistics AS
  SELECT strftime('%Y-%m', date) period, r.dept_id, dept_name, empl_id, realname,
  sum(CASE WHEN r.type = 1 THEN duration ELSE 0 END) overtime,
  sum(CASE WHEN r.type = 0 THEN 0 - duration ELSE 0 END) leave,
  sum(duration) summary
  FROM record r
  JOIN department d ON d.id = r.dept_id
  JOIN employee e ON e.id = empl_id
  WHERE status = 1
  GROUP BY period, r.dept_id, empl_id
  ORDER BY period DESC;

INSERT INTO employee (id, username, realname, password, type, dept_id)
  VALUES (0, 'admin', 'admin', 'pbkdf2:sha256:50000$UlmUcYy1$5331b54a654bb31f10098cbe566a50a30f0aad0b13a9a8ce1ce6efaf14bb6959', 1, 0);