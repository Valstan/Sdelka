# File: app/core/database/queries.py

class ContractQueries:
    CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contract_number TEXT UNIQUE NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    INSERT = """
    INSERT INTO contracts (contract_number, start_date, end_date, description)
    VALUES (?, ?, ?, ?);
    """

    SELECT_ALL = "SELECT * FROM contracts;"
    SELECT_BY_ID = "SELECT * FROM contracts WHERE id = ?;"
    UPDATE = """
    UPDATE contracts
    SET contract_number = ?, start_date = ?, end_date = ?, description = ?
    WHERE id = ?;
    """
    DELETE = "DELETE FROM contracts WHERE id = ?;"