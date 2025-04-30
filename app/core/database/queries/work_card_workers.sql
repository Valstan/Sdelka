-- Таблица работников по нарядам
CREATE TABLE IF NOT EXISTS work_card_workers (
    work_card_id INTEGER REFERENCES work_cards(id) ON DELETE CASCADE,
    worker_id INTEGER REFERENCES workers(id) ON DELETE CASCADE,
    amount REAL DEFAULT 0 CHECK(amount >= 0),
    PRIMARY KEY(work_card_id, worker_id)
);

-- Индекс по работнику для отчетности
CREATE INDEX IF NOT EXISTS idx_worker_id ON work_card_workers(worker_id);