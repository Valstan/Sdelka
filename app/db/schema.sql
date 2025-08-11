-- Schema DDL only
CREATE TABLE IF NOT EXISTS workers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  last_name TEXT NOT NULL,
  first_name TEXT NOT NULL,
  middle_name TEXT,
  position TEXT,
  phone TEXT,
  hire_date TEXT,
  is_active INTEGER NOT NULL DEFAULT 1,
  UNIQUE(last_name, first_name, middle_name)
);

CREATE TABLE IF NOT EXISTS job_types (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  unit TEXT NOT NULL,
  base_rate REAL NOT NULL CHECK(base_rate >= 0)
);

CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  sku TEXT UNIQUE,
  description TEXT
);

CREATE TABLE IF NOT EXISTS contracts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  contract_number TEXT NOT NULL UNIQUE,
  customer TEXT NOT NULL,
  start_date TEXT NOT NULL,
  end_date TEXT,
  status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','completed','cancelled'))
);

CREATE TABLE IF NOT EXISTS work_orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  contract_id INTEGER NOT NULL,
  worker_id INTEGER NOT NULL,
  job_type_id INTEGER NOT NULL,
  product_id INTEGER,
  date TEXT NOT NULL,
  quantity REAL NOT NULL CHECK(quantity > 0),
  unit_rate REAL NOT NULL CHECK(unit_rate >= 0),
  amount REAL NOT NULL,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(contract_id) REFERENCES contracts(id) ON DELETE RESTRICT,
  FOREIGN KEY(worker_id) REFERENCES workers(id) ON DELETE RESTRICT,
  FOREIGN KEY(job_type_id) REFERENCES job_types(id) ON DELETE RESTRICT,
  FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_work_orders_date ON work_orders(date);
CREATE INDEX IF NOT EXISTS idx_work_orders_worker ON work_orders(worker_id);
CREATE INDEX IF NOT EXISTS idx_work_orders_contract ON work_orders(contract_id);