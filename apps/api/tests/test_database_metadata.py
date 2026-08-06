import warnings

from sqlalchemy.exc import SAWarning

from app.domain.models import Base


def test_metadata_has_no_unresolvable_foreign_key_cycles() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", SAWarning)
        sorted(Base.metadata.sorted_tables, key=lambda table: table.name)


def test_internship_unique_indexes_match_the_database_contract() -> None:
    expected_unique_indexes = {
        "internship_programs": "ix_internship_programs_slug",
        "internship_tracks": "ix_internship_tracks_slug",
        "internship_uploads": "ix_internship_uploads_upload_id",
    }

    for table_name, index_name in expected_unique_indexes.items():
        index = next(
            index for index in Base.metadata.tables[table_name].indexes if index.name == index_name
        )
        assert index.unique

    draft_index = next(
        index
        for index in Base.metadata.tables["internship_submissions"].indexes
        if index.name == "uq_internship_submissions_one_active_draft"
    )
    assert draft_index.unique
    assert str(draft_index.dialect_options["postgresql"]["where"]) == "state = 'DRAFT'"
    assert str(draft_index.dialect_options["sqlite"]["where"]) == "state = 'DRAFT'"
