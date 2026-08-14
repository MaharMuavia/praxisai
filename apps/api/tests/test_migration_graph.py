from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_internship_migration_branch_precedes_completion_concurrency() -> None:
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    script = ScriptDirectory.from_config(config)

    assert script.get_heads() == ["c3d4e5f6a7b8"]
    assert script.get_revision("f5a1b2c3d4e5").down_revision == "d1e2f3a4b5c6"
    assert script.get_revision("c3d4e5f6a7b8").down_revision == "c2d3e4f5a6b7"
