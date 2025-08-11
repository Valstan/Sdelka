from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from app.db.migrations import destroy_database_for_tests, initialize_database
from app.db.repository import Repository
from app.services.contracts_service import ContractsService
from app.services.job_types_service import JobTypesService
from app.services.work_orders_service import WorkOrdersService
from app.services.workers_service import WorkersService
from app.utils.backup import backup_database_with_rotation
from app.utils.paths import get_paths


def setup_function(_):
    destroy_database_for_tests()


def test_db_init_and_backup(tmp_path):
    initialize_database()
    paths = get_paths()
    assert paths.db_file.exists()
    backup = backup_database_with_rotation(max_copies=2)
    assert backup.exists()


def test_services_crud_flow():
    initialize_database()
    repo = Repository()

    workers = WorkersService(repo)
    job_types = JobTypesService(repo)
    contracts = ContractsService(repo)
    work_orders = WorkOrdersService(repo)

    wid = workers.create_worker("Иванов", "Иван")
    jid = job_types.create_job_type("Сборка", "шт", 10.0)
    cid = contracts.create_contract("C-001", "ООО Ромашка", "2024-01-01")

    wo_id = work_orders.create_work_order(cid, wid, jid, None, "2024-01-10", 5, 12.5)
    assert wo_id > 0

    all_wo = work_orders.list_work_orders()
    assert len(all_wo) == 1
    assert all_wo[0]["amount"] == 62.5

    df = pd.DataFrame(all_wo)
    assert not df.empty