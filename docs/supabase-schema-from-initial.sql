BEGIN;

-- Running upgrade fdeefd043d61 -> 6a9b88a3be4c

CREATE TABLE analytics_events (
    event_type VARCHAR(80) NOT NULL, 
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    environment VARCHAR(20) NOT NULL, 
    is_demo BOOLEAN NOT NULL, 
    payload JSON NOT NULL, 
    exported_at TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_analytics_events_event_type ON analytics_events (event_type);

CREATE TABLE feature_flags (
    name VARCHAR(100) NOT NULL, 
    enabled BOOLEAN NOT NULL, 
    environment VARCHAR(20) NOT NULL, 
    reason TEXT NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (name)
);

CREATE TABLE matching_configurations (
    version INTEGER NOT NULL, 
    weights JSON NOT NULL, 
    active_from TIMESTAMP WITH TIME ZONE NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (version)
);

CREATE TABLE rate_cards (
    version INTEGER NOT NULL, 
    currency VARCHAR(3) NOT NULL, 
    entries JSON NOT NULL, 
    active_from TIMESTAMP WITH TIME ZONE NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (version)
);

CREATE TABLE retention_configurations (
    record_type VARCHAR(80) NOT NULL, 
    retention_days INTEGER NOT NULL, 
    legal_review_required BOOLEAN NOT NULL, 
    active_from TIMESTAMP WITH TIME ZONE NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (record_type)
);

CREATE TABLE export_jobs (
    organization_id UUID NOT NULL, 
    requested_by_id UUID NOT NULL, 
    purpose TEXT NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    storage_key VARCHAR(500), 
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    FOREIGN KEY(requested_by_id) REFERENCES users (id)
);

CREATE INDEX ix_export_jobs_organization_id ON export_jobs (organization_id);

CREATE TABLE invitations (
    organization_id UUID NOT NULL, 
    email VARCHAR(320) NOT NULL, 
    role VARCHAR(40) NOT NULL, 
    token_hash VARCHAR(64) NOT NULL, 
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    accepted_at TIMESTAMP WITH TIME ZONE, 
    revoked_at TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    UNIQUE (token_hash)
);

CREATE INDEX ix_invitations_email ON invitations (email);

CREATE INDEX ix_invitations_organization_id ON invitations (organization_id);

CREATE TABLE client_verifications (
    client_profile_id UUID NOT NULL, 
    status VARCHAR(32) NOT NULL, 
    evidence JSON NOT NULL, 
    reviewed_by_id UUID, 
    reviewed_at TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(client_profile_id) REFERENCES client_profiles (id), 
    FOREIGN KEY(reviewed_by_id) REFERENCES users (id)
);

CREATE INDEX ix_client_verifications_client_profile_id ON client_verifications (client_profile_id);

CREATE TABLE institutional_agreements (
    university_id UUID NOT NULL, 
    version INTEGER NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    entitlements JSON NOT NULL, 
    starts_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    ends_at TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(university_id) REFERENCES universities (id)
);

CREATE INDEX ix_institutional_agreements_university_id ON institutional_agreements (university_id);

CREATE TABLE project_comments (
    project_id UUID NOT NULL, 
    author_id UUID NOT NULL, 
    visibility VARCHAR(30) NOT NULL, 
    body TEXT NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(author_id) REFERENCES users (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE INDEX ix_project_comments_project_id ON project_comments (project_id);

CREATE TABLE project_risks (
    project_id UUID NOT NULL, 
    source VARCHAR(30) NOT NULL, 
    summary TEXT NOT NULL, 
    confidence VARCHAR(20) NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    human_decision VARCHAR(30), 
    decided_by_id UUID, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(decided_by_id) REFERENCES users (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE INDEX ix_project_risks_project_id ON project_risks (project_id);

CREATE TABLE plan_runs (
    project_id UUID NOT NULL, 
    scope_version_id UUID NOT NULL, 
    agent_run_id UUID NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    plan_snapshot JSON NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(agent_run_id) REFERENCES agent_runs (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(scope_version_id) REFERENCES project_scope_versions (id)
);

CREATE INDEX ix_plan_runs_project_id ON plan_runs (project_id);

UPDATE alembic_version SET version_num='6a9b88a3be4c' WHERE alembic_version.version_num = 'fdeefd043d61';

-- Running upgrade 6a9b88a3be4c -> a13f4c62e908

CREATE TABLE credential_revocations (
    credential_id UUID NOT NULL, 
    revoked_by_id UUID NOT NULL, 
    reason TEXT NOT NULL, 
    idempotency_key VARCHAR(128) NOT NULL, 
    revoked_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(credential_id) REFERENCES credentials (id), 
    FOREIGN KEY(revoked_by_id) REFERENCES users (id), 
    UNIQUE (credential_id), 
    UNIQUE (idempotency_key)
);

CREATE UNIQUE INDEX ix_credential_revocations_credential_id ON credential_revocations (credential_id);

CREATE INDEX ix_credential_revocations_revoked_by_id ON credential_revocations (revoked_by_id);

UPDATE alembic_version SET version_num='a13f4c62e908' WHERE alembic_version.version_num = '6a9b88a3be4c';

-- Running upgrade a13f4c62e908 -> c4e7d0a621b2

ALTER TABLE export_jobs ADD COLUMN idempotency_key VARCHAR(128);

ALTER TABLE export_jobs ADD CONSTRAINT uq_export_jobs_idempotency_key UNIQUE (idempotency_key);

UPDATE export_jobs SET idempotency_key = 'legacy-' || CAST(id AS VARCHAR) WHERE idempotency_key IS NULL;

ALTER TABLE export_jobs ALTER COLUMN idempotency_key SET NOT NULL;

CREATE TABLE job_attempts (
    outbox_event_id UUID NOT NULL, 
    attempt_number INTEGER NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    started_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    finished_at TIMESTAMP WITH TIME ZONE, 
    error_category VARCHAR(100), 
    error_message TEXT, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(outbox_event_id) REFERENCES outbox_events (id), 
    UNIQUE (outbox_event_id, attempt_number)
);

CREATE INDEX ix_job_attempts_outbox_event_id ON job_attempts (outbox_event_id);

CREATE INDEX ix_job_attempts_status ON job_attempts (status);

CREATE TABLE outbox_recoveries (
    outbox_event_id UUID NOT NULL, 
    recovered_by_id UUID NOT NULL, 
    reason TEXT NOT NULL, 
    idempotency_key VARCHAR(128) NOT NULL, 
    recovered_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(outbox_event_id) REFERENCES outbox_events (id), 
    FOREIGN KEY(recovered_by_id) REFERENCES users (id), 
    UNIQUE (idempotency_key)
);

CREATE INDEX ix_outbox_recoveries_outbox_event_id ON outbox_recoveries (outbox_event_id);

CREATE INDEX ix_outbox_recoveries_recovered_by_id ON outbox_recoveries (recovered_by_id);

UPDATE alembic_version SET version_num='c4e7d0a621b2' WHERE alembic_version.version_num = 'a13f4c62e908';

-- Running upgrade c4e7d0a621b2 -> d59e10bf2c83

ALTER TABLE notifications ADD COLUMN source_outbox_event_id UUID;

ALTER TABLE notifications ADD CONSTRAINT fk_notifications_source_outbox_event_id FOREIGN KEY(source_outbox_event_id) REFERENCES outbox_events (id);

ALTER TABLE notifications ADD CONSTRAINT uq_notifications_user_source_event UNIQUE (user_id, source_outbox_event_id);

CREATE INDEX ix_notifications_source_outbox_event_id ON notifications (source_outbox_event_id);

CREATE TABLE notification_preferences (
    user_id UUID NOT NULL, 
    category VARCHAR(40) NOT NULL, 
    enabled BOOLEAN NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id), 
    UNIQUE (user_id, category)
);

CREATE INDEX ix_notification_preferences_user_id ON notification_preferences (user_id);

CREATE TABLE provider_synchronizations (
    provider VARCHAR(60) NOT NULL, 
    operation VARCHAR(80) NOT NULL, 
    mode VARCHAR(30) NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    resource_type VARCHAR(60) NOT NULL, 
    resource_id UUID, 
    correlation_id UUID NOT NULL, 
    error_category VARCHAR(100), 
    details JSON NOT NULL, 
    checked_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_provider_synchronizations_provider ON provider_synchronizations (provider);

CREATE INDEX ix_provider_synchronizations_status ON provider_synchronizations (status);

CREATE INDEX ix_provider_synchronizations_resource_id ON provider_synchronizations (resource_id);

CREATE INDEX ix_provider_synchronizations_correlation_id ON provider_synchronizations (correlation_id);

UPDATE alembic_version SET version_num='d59e10bf2c83' WHERE alembic_version.version_num = 'c4e7d0a621b2';

-- Running upgrade d59e10bf2c83 -> e7b3c8f2a109

ALTER TABLE assignment_offers ADD COLUMN decision_idempotency_key VARCHAR(128);

CREATE UNIQUE INDEX ix_assignment_offers_decision_idempotency_key ON assignment_offers (decision_idempotency_key);

UPDATE alembic_version SET version_num='e7b3c8f2a109' WHERE alembic_version.version_num = 'd59e10bf2c83';

-- Running upgrade e7b3c8f2a109 -> f4c2d1a9b807

ALTER TABLE payouts ADD COLUMN evidence_hash VARCHAR(64);

ALTER TABLE payouts ADD COLUMN idempotency_key VARCHAR(128);

CREATE UNIQUE INDEX ix_payouts_idempotency_key ON payouts (idempotency_key);

DROP INDEX ix_payouts_allocation_id;

CREATE UNIQUE INDEX ix_payouts_allocation_id ON payouts (allocation_id);

UPDATE alembic_version SET version_num='f4c2d1a9b807' WHERE alembic_version.version_num = 'e7b3c8f2a109';

-- Running upgrade f4c2d1a9b807 -> b7d9e4a1c302

CREATE TABLE learning_paths (
    slug VARCHAR(100) NOT NULL, 
    title VARCHAR(200) NOT NULL, 
    summary TEXT NOT NULL, 
    level VARCHAR(30) NOT NULL, 
    estimated_hours INTEGER NOT NULL, 
    skill_outcomes JSON NOT NULL, 
    prerequisites JSON NOT NULL, 
    active BOOLEAN NOT NULL, 
    is_demo BOOLEAN NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CHECK (estimated_hours > 0), 
    UNIQUE (slug)
);

CREATE UNIQUE INDEX ix_learning_paths_slug ON learning_paths (slug);

CREATE INDEX ix_learning_paths_active ON learning_paths (active);

CREATE TABLE learning_modules (
    learning_path_id UUID NOT NULL, 
    ordinal INTEGER NOT NULL, 
    title VARCHAR(200) NOT NULL, 
    summary TEXT NOT NULL, 
    estimated_minutes INTEGER NOT NULL, 
    content_sections JSON NOT NULL, 
    exercise_brief TEXT NOT NULL, 
    completion_evidence TEXT NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(learning_path_id) REFERENCES learning_paths (id), 
    UNIQUE (learning_path_id, ordinal)
);

CREATE INDEX ix_learning_modules_learning_path_id ON learning_modules (learning_path_id);

CREATE TABLE learning_enrollments (
    learning_path_id UUID NOT NULL, 
    student_user_id UUID NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    enrolled_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    completed_at TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(learning_path_id) REFERENCES learning_paths (id), 
    FOREIGN KEY(student_user_id) REFERENCES users (id), 
    UNIQUE (learning_path_id, student_user_id)
);

CREATE INDEX ix_learning_enrollments_learning_path_id ON learning_enrollments (learning_path_id);

CREATE INDEX ix_learning_enrollments_student_user_id ON learning_enrollments (student_user_id);

CREATE TABLE learning_module_completions (
    enrollment_id UUID NOT NULL, 
    learning_module_id UUID NOT NULL, 
    evidence_summary TEXT NOT NULL, 
    completed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(enrollment_id) REFERENCES learning_enrollments (id), 
    FOREIGN KEY(learning_module_id) REFERENCES learning_modules (id), 
    UNIQUE (enrollment_id, learning_module_id)
);

CREATE INDEX ix_learning_module_completions_enrollment_id ON learning_module_completions (enrollment_id);

CREATE INDEX ix_learning_module_completions_learning_module_id ON learning_module_completions (learning_module_id);

CREATE TABLE project_opportunities (
    project_id UUID NOT NULL, 
    published_by_id UUID NOT NULL, 
    headline VARCHAR(200) NOT NULL, 
    brief TEXT NOT NULL, 
    required_skills JSON NOT NULL, 
    nice_to_have_skills JSON NOT NULL, 
    deliverables JSON NOT NULL, 
    proposal_requirements JSON NOT NULL, 
    estimated_hours_low INTEGER NOT NULL, 
    estimated_hours_high INTEGER NOT NULL, 
    budget_minor INTEGER NOT NULL, 
    currency VARCHAR(3) NOT NULL, 
    deadline TIMESTAMP WITH TIME ZONE NOT NULL, 
    supervision_level VARCHAR(30) NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    max_proposals INTEGER NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CHECK (estimated_hours_low > 0), 
    CHECK (estimated_hours_high >= estimated_hours_low), 
    CHECK (budget_minor > 0), 
    CHECK (max_proposals > 0), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(published_by_id) REFERENCES users (id), 
    UNIQUE (project_id)
);

CREATE UNIQUE INDEX ix_project_opportunities_project_id ON project_opportunities (project_id);

CREATE INDEX ix_project_opportunities_published_by_id ON project_opportunities (published_by_id);

CREATE INDEX ix_project_opportunities_status ON project_opportunities (status);

CREATE TABLE student_proposals (
    opportunity_id UUID NOT NULL, 
    student_user_id UUID NOT NULL, 
    cover_note TEXT NOT NULL, 
    approach TEXT NOT NULL, 
    delivery_plan JSON NOT NULL, 
    relevant_evidence JSON NOT NULL, 
    proposed_amount_minor INTEGER NOT NULL, 
    currency VARCHAR(3) NOT NULL, 
    estimated_days INTEGER NOT NULL, 
    availability_hours_per_week INTEGER NOT NULL, 
    state VARCHAR(30) NOT NULL, 
    submission_idempotency_key VARCHAR(128) NOT NULL, 
    submission_hash VARCHAR(64) NOT NULL, 
    decided_by_id UUID, 
    decision_reason TEXT, 
    decided_at TIMESTAMP WITH TIME ZONE, 
    decision_idempotency_key VARCHAR(128), 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CHECK (proposed_amount_minor > 0), 
    CHECK (estimated_days > 0), 
    CHECK (availability_hours_per_week > 0), 
    FOREIGN KEY(decided_by_id) REFERENCES users (id), 
    FOREIGN KEY(opportunity_id) REFERENCES project_opportunities (id), 
    FOREIGN KEY(student_user_id) REFERENCES users (id), 
    UNIQUE (opportunity_id, student_user_id)
);

CREATE INDEX ix_student_proposals_opportunity_id ON student_proposals (opportunity_id);

CREATE INDEX ix_student_proposals_student_user_id ON student_proposals (student_user_id);

CREATE INDEX ix_student_proposals_state ON student_proposals (state);

CREATE UNIQUE INDEX ix_student_proposals_submission_idempotency_key ON student_proposals (submission_idempotency_key);

CREATE UNIQUE INDEX ix_student_proposals_decision_idempotency_key ON student_proposals (decision_idempotency_key);

UPDATE alembic_version SET version_num='b7d9e4a1c302' WHERE alembic_version.version_num = 'f4c2d1a9b807';

-- Running upgrade b7d9e4a1c302 -> c8f1a2d4e609

ALTER TABLE credential_revocations DROP CONSTRAINT credential_revocations_credential_id_key;

ALTER TABLE learning_paths DROP CONSTRAINT learning_paths_slug_key;

ALTER TABLE project_opportunities DROP CONSTRAINT project_opportunities_project_id_key;

UPDATE alembic_version SET version_num='c8f1a2d4e609' WHERE alembic_version.version_num = 'b7d9e4a1c302';

COMMIT;

