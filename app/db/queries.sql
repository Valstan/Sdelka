-- workers CRUD
-- [workers.insert]
INSERT INTO workers(last_name, first_name, middle_name, position, phone, hire_date, is_active)
VALUES(?,?,?,?,?,?,?);
-- [workers.update]
UPDATE workers SET last_name=?, first_name=?, middle_name=?, position=?, phone=?, hire_date=?, is_active=?
WHERE id=?;
-- [workers.delete]
DELETE FROM workers WHERE id=?;
-- [workers.select_all]
SELECT * FROM workers ORDER BY last_name, first_name, middle_name;
-- [workers.select_active]
SELECT * FROM workers WHERE is_active=1 ORDER BY last_name, first_name, middle_name;

-- job_types CRUD
-- [job_types.insert]
INSERT INTO job_types(name, unit, base_rate) VALUES(?,?,?);
-- [job_types.update]
UPDATE job_types SET name=?, unit=?, base_rate=? WHERE id=?;
-- [job_types.delete]
DELETE FROM job_types WHERE id=?;
-- [job_types.select_all]
SELECT * FROM job_types ORDER BY name;

-- products CRUD
-- [products.insert]
INSERT INTO products(name, sku, description) VALUES(?,?,?);
-- [products.update]
UPDATE products SET name=?, sku=?, description=? WHERE id=?;
-- [products.delete]
DELETE FROM products WHERE id=?;
-- [products.select_all]
SELECT * FROM products ORDER BY name;

-- contracts CRUD
-- [contracts.insert]
INSERT INTO contracts(contract_number, customer, start_date, end_date, status) VALUES(?,?,?,?,?);
-- [contracts.update]
UPDATE contracts SET contract_number=?, customer=?, start_date=?, end_date=?, status=? WHERE id=?;
-- [contracts.delete]
DELETE FROM contracts WHERE id=?;
-- [contracts.select_all]
SELECT * FROM contracts ORDER BY start_date DESC;

-- work_orders CRUD
-- [work_orders.insert]
INSERT INTO work_orders(contract_id, worker_id, job_type_id, product_id, date, quantity, unit_rate, amount, notes)
VALUES(?,?,?,?,?,?,?,?,?);
-- [work_orders.update]
UPDATE work_orders SET contract_id=?, worker_id=?, job_type_id=?, product_id=?, date=?, quantity=?, unit_rate=?, amount=?, notes=? WHERE id=?;
-- [work_orders.delete]
DELETE FROM work_orders WHERE id=?;
-- [work_orders.select_all]
SELECT * FROM work_orders ORDER BY date DESC, id DESC;
-- [work_orders.select_filtered]
SELECT wo.*, w.last_name, w.first_name, jt.name as job_name, p.name as product_name, c.contract_number
FROM work_orders wo
JOIN workers w ON w.id = wo.worker_id
JOIN job_types jt ON jt.id = wo.job_type_id
LEFT JOIN products p ON p.id = wo.product_id
JOIN contracts c ON c.id = wo.contract_id
WHERE (wo.date BETWEEN ? AND ?) AND (? IS NULL OR wo.worker_id = ?) AND (? IS NULL OR wo.contract_id = ?)
ORDER BY wo.date DESC;