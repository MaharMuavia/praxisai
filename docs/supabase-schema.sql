BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> fdeefd043d61

CREATE TABLE organizations (
    name VARCHAR(200) NOT NULL, 
    slug VARCHAR(100) NOT NULL, 
    kind VARCHAR(40) NOT NULL, 
    is_demo BOOLEAN NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_organizations_slug ON organizations (slug);

CREATE TABLE outbox_events (
    event_type VARCHAR(80) NOT NULL, 
    aggregate_type VARCHAR(60) NOT NULL, 
    aggregate_id UUID NOT NULL, 
    payload JSON NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    attempts INTEGER NOT NULL, 
    available_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    last_error TEXT, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_outbox_events_aggregate_id ON outbox_events (aggregate_id);

CREATE INDEX ix_outbox_events_event_type ON outbox_events (event_type);

CREATE INDEX ix_outbox_events_status ON outbox_events (status);

CREATE TABLE policy_versions (
    policy_name VARCHAR(100) NOT NULL, 
    version INTEGER NOT NULL, 
    payload JSON NOT NULL, 
    active_from TIMESTAMP WITH TIME ZONE NOT NULL, 
    is_demo BOOLEAN NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (policy_name, version)
);

CREATE TABLE prompt_versions (
    agent_name VARCHAR(50) NOT NULL, 
    version VARCHAR(40) NOT NULL, 
    template TEXT NOT NULL, 
    active BOOLEAN NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (agent_name, version)
);

CREATE INDEX ix_prompt_versions_agent_name ON prompt_versions (agent_name);

CREATE TABLE rate_limit_buckets (
    bucket_key VARCHAR(128) NOT NULL, 
    window_started_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    request_count INTEGER NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (bucket_key)
);

CREATE TABLE skills (
    name VARCHAR(100) NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (name)
);

CREATE TABLE users (
    email VARCHAR(320) NOT NULL, 
    display_name VARCHAR(160) NOT NULL, 
    external_subject VARCHAR(255), 
    is_active BOOLEAN NOT NULL, 
    is_demo BOOLEAN NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (external_subject)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE TABLE audit_events (
    actor_id UUID, 
    organization_id UUID, 
    action VARCHAR(100) NOT NULL, 
    resource_type VARCHAR(80) NOT NULL, 
    resource_id UUID, 
    correlation_id UUID NOT NULL, 
    payload JSON NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(actor_id) REFERENCES users (id), 
    FOREIGN KEY(organization_id) REFERENCES organizations (id)
);

CREATE INDEX ix_audit_events_action ON audit_events (action);

CREATE INDEX ix_audit_events_actor_id ON audit_events (actor_id);

CREATE INDEX ix_audit_events_correlation_id ON audit_events (correlation_id);

CREATE INDEX ix_audit_events_organization_id ON audit_events (organization_id);

CREATE INDEX ix_audit_events_resource_id ON audit_events (resource_id);

CREATE TABLE client_profiles (
    user_id UUID NOT NULL, 
    organization_id UUID NOT NULL, 
    verification_status VARCHAR(32) NOT NULL, 
    billing_country VARCHAR(2), 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    FOREIGN KEY(user_id) REFERENCES users (id), 
    UNIQUE (user_id)
);

CREATE INDEX ix_client_profiles_organization_id ON client_profiles (organization_id);

CREATE TABLE consent_records (
    user_id UUID NOT NULL, 
    consent_type VARCHAR(60) NOT NULL, 
    version VARCHAR(30) NOT NULL, 
    granted BOOLEAN NOT NULL, 
    snapshot JSON NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_consent_records_user_id ON consent_records (user_id);

CREATE TABLE lead_profiles (
    user_id UUID NOT NULL, 
    domains JSON NOT NULL, 
    verified BOOLEAN NOT NULL, 
    workload_cap_hours INTEGER NOT NULL, 
    committed_hours INTEGER NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id), 
    UNIQUE (user_id)
);

CREATE TABLE notifications (
    user_id UUID NOT NULL, 
    kind VARCHAR(50) NOT NULL, 
    title VARCHAR(160) NOT NULL, 
    body TEXT NOT NULL, 
    resource_path VARCHAR(500), 
    read_at TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_notifications_user_id ON notifications (user_id);

CREATE TABLE organization_memberships (
    user_id UUID NOT NULL, 
    organization_id UUID NOT NULL, 
    role VARCHAR(40) NOT NULL, 
    is_active BOOLEAN NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    FOREIGN KEY(user_id) REFERENCES users (id), 
    UNIQUE (user_id, organization_id, role)
);

CREATE INDEX ix_organization_memberships_organization_id ON organization_memberships (organization_id);

CREATE INDEX ix_organization_memberships_role ON organization_memberships (role);

CREATE INDEX ix_organization_memberships_user_id ON organization_memberships (user_id);

CREATE TABLE projects (
    client_organization_id UUID NOT NULL, 
    created_by_id UUID NOT NULL, 
    title VARCHAR(200) NOT NULL, 
    description TEXT NOT NULL, 
    category VARCHAR(80) NOT NULL, 
    state VARCHAR(64) NOT NULL, 
    version INTEGER NOT NULL, 
    required_deposit_minor INTEGER NOT NULL, 
    funded_minor INTEGER NOT NULL, 
    currency VARCHAR(3) NOT NULL, 
    complexity VARCHAR(20) NOT NULL, 
    is_demo BOOLEAN NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    CHECK (funded_minor >= 0), 
    CHECK (required_deposit_minor >= 0), 
    FOREIGN KEY(client_organization_id) REFERENCES organizations (id), 
    FOREIGN KEY(created_by_id) REFERENCES users (id)
);

CREATE INDEX ix_projects_client_organization_id ON projects (client_organization_id);

CREATE INDEX ix_projects_created_by_id ON projects (created_by_id);

CREATE INDEX ix_projects_state ON projects (state);

CREATE TABLE student_profiles (
    user_id UUID NOT NULL, 
    bio TEXT NOT NULL, 
    timezone VARCHAR(80) NOT NULL, 
    eligible BOOLEAN NOT NULL, 
    confirmed_18_plus BOOLEAN NOT NULL, 
    workload_cap_hours INTEGER NOT NULL, 
    committed_hours INTEGER NOT NULL, 
    completed_projects INTEGER NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id), 
    UNIQUE (user_id)
);

CREATE TABLE universities (
    organization_id UUID NOT NULL, 
    agreement_status VARCHAR(32) NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(organization_id) REFERENCES organizations (id), 
    UNIQUE (organization_id)
);

CREATE TABLE agent_runs (
    project_id UUID, 
    agent_name VARCHAR(50) NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    model_identifier VARCHAR(120), 
    prompt_version VARCHAR(40) NOT NULL, 
    input_snapshot_hash VARCHAR(64) NOT NULL, 
    input_summary JSON NOT NULL, 
    output JSON, 
    validation_status VARCHAR(30) NOT NULL, 
    latency_ms INTEGER, 
    retry_count INTEGER NOT NULL, 
    usage JSON, 
    error_category VARCHAR(60), 
    correlation_id UUID NOT NULL, 
    is_demo BOOLEAN NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE INDEX ix_agent_runs_agent_name ON agent_runs (agent_name);

CREATE INDEX ix_agent_runs_correlation_id ON agent_runs (correlation_id);

CREATE INDEX ix_agent_runs_project_id ON agent_runs (project_id);

CREATE INDEX ix_agent_runs_project_status ON agent_runs (project_id, status);

CREATE INDEX ix_agent_runs_status ON agent_runs (status);

CREATE TABLE appeals (
    appellant_id UUID NOT NULL, 
    project_id UUID NOT NULL, 
    decision_type VARCHAR(50) NOT NULL, 
    decision_id UUID NOT NULL, 
    state VARCHAR(40) NOT NULL, 
    decision_snapshot JSON NOT NULL, 
    reviewer_id UUID, 
    resolution_reason TEXT, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(appellant_id) REFERENCES users (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(reviewer_id) REFERENCES users (id)
);

CREATE INDEX ix_appeals_appellant_id ON appeals (appellant_id);

CREATE INDEX ix_appeals_project_id ON appeals (project_id);

CREATE TABLE approvals (
    project_id UUID NOT NULL, 
    subject_type VARCHAR(40) NOT NULL, 
    subject_id UUID NOT NULL, 
    decision VARCHAR(20) NOT NULL, 
    actor_id UUID NOT NULL, 
    reason TEXT NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(actor_id) REFERENCES users (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE INDEX ix_approvals_project_id ON approvals (project_id);

CREATE INDEX ix_approvals_subject_id ON approvals (subject_id);

CREATE TABLE assignment_offers (
    project_id UUID NOT NULL, 
    recipient_user_id UUID NOT NULL, 
    role VARCHAR(50) NOT NULL, 
    state VARCHAR(30) NOT NULL, 
    terms_snapshot JSON NOT NULL, 
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    decided_at TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(recipient_user_id) REFERENCES users (id)
);

CREATE INDEX ix_assignment_offers_project_id ON assignment_offers (project_id);

CREATE INDEX ix_assignment_offers_recipient_user_id ON assignment_offers (recipient_user_id);

CREATE TABLE availability_windows (
    student_profile_id UUID NOT NULL, 
    starts_on DATE NOT NULL, 
    ends_on DATE NOT NULL, 
    hours_per_week INTEGER NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(student_profile_id) REFERENCES student_profiles (id)
);

CREATE INDEX ix_availability_windows_student_profile_id ON availability_windows (student_profile_id);

CREATE TABLE change_orders (
    project_id UUID NOT NULL, 
    version INTEGER NOT NULL, 
    state VARCHAR(40) NOT NULL, 
    scope_diff JSON NOT NULL, 
    added_compensation_minor INTEGER NOT NULL, 
    added_days INTEGER NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE INDEX ix_change_orders_project_id ON change_orders (project_id);

CREATE TABLE check_ins (
    project_id UUID NOT NULL, 
    student_user_id UUID NOT NULL, 
    progress TEXT NOT NULL, 
    next_step TEXT NOT NULL, 
    blocker TEXT, 
    help_needed TEXT, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(student_user_id) REFERENCES users (id)
);

CREATE INDEX ix_check_ins_project_id ON check_ins (project_id);

CREATE INDEX ix_check_ins_student_user_id ON check_ins (student_user_id);

CREATE TABLE credentials (
    student_user_id UUID NOT NULL, 
    project_id UUID NOT NULL, 
    public_slug VARCHAR(80) NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    schema_version VARCHAR(20) NOT NULL, 
    canonical_payload JSON NOT NULL, 
    payload_hash VARCHAR(64) NOT NULL, 
    signature TEXT NOT NULL, 
    key_identifier VARCHAR(255) NOT NULL, 
    consent_snapshot JSON NOT NULL, 
    issued_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    revoked_at TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(student_user_id) REFERENCES users (id)
);

CREATE INDEX ix_credentials_project_id ON credentials (project_id);

CREATE UNIQUE INDEX ix_credentials_public_slug ON credentials (public_slug);

CREATE INDEX ix_credentials_student_user_id ON credentials (student_user_id);

CREATE TABLE deliverables (
    project_id UUID NOT NULL, 
    submitted_by_id UUID NOT NULL, 
    title VARCHAR(200) NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    version INTEGER NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(submitted_by_id) REFERENCES users (id)
);

CREATE INDEX ix_deliverables_project_id ON deliverables (project_id);

CREATE TABLE disputes (
    project_id UUID NOT NULL, 
    opened_by_id UUID NOT NULL, 
    state VARCHAR(30) NOT NULL, 
    category VARCHAR(50) NOT NULL, 
    summary TEXT NOT NULL, 
    reviewer_id UUID, 
    resolution TEXT, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(opened_by_id) REFERENCES users (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(reviewer_id) REFERENCES users (id)
);

CREATE INDEX ix_disputes_project_id ON disputes (project_id);

CREATE TABLE invoices (
    project_id UUID NOT NULL, 
    number VARCHAR(60) NOT NULL, 
    amount_minor INTEGER NOT NULL, 
    currency VARCHAR(3) NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    environment VARCHAR(20) NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    UNIQUE (number)
);

CREATE INDEX ix_invoices_project_id ON invoices (project_id);

CREATE TABLE ledger_entries (
    transaction_id UUID NOT NULL, 
    project_id UUID NOT NULL, 
    account VARCHAR(80) NOT NULL, 
    amount_minor INTEGER NOT NULL, 
    currency VARCHAR(3) NOT NULL, 
    memo VARCHAR(255) NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE INDEX ix_ledger_entries_project_id ON ledger_entries (project_id);

CREATE INDEX ix_ledger_entries_transaction_id ON ledger_entries (transaction_id);

CREATE TABLE milestones (
    project_id UUID NOT NULL, 
    title VARCHAR(200) NOT NULL, 
    ordinal INTEGER NOT NULL, 
    due_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE INDEX ix_milestones_project_id ON milestones (project_id);

CREATE TABLE payment_events (
    provider VARCHAR(30) NOT NULL, 
    provider_event_id VARCHAR(255) NOT NULL, 
    project_id UUID, 
    event_type VARCHAR(80) NOT NULL, 
    environment VARCHAR(20) NOT NULL, 
    payload_hash VARCHAR(64) NOT NULL, 
    processed_at TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    UNIQUE (provider_event_id)
);

CREATE INDEX ix_payment_events_project_id ON payment_events (project_id);

CREATE TABLE payout_allocations (
    project_id UUID NOT NULL, 
    recipient_user_id UUID NOT NULL, 
    amount_minor INTEGER NOT NULL, 
    currency VARCHAR(3) NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    approved_by_id UUID, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(approved_by_id) REFERENCES users (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(recipient_user_id) REFERENCES users (id)
);

CREATE INDEX ix_payout_allocations_project_id ON payout_allocations (project_id);

CREATE INDEX ix_payout_allocations_recipient_user_id ON payout_allocations (recipient_user_id);

CREATE TABLE portfolio_permissions (
    project_id UUID NOT NULL, 
    student_user_id UUID NOT NULL, 
    client_name_allowed BOOLEAN NOT NULL, 
    project_title_allowed BOOLEAN NOT NULL, 
    screenshots_allowed BOOLEAN NOT NULL, 
    repository_allowed BOOLEAN NOT NULL, 
    deployment_allowed BOOLEAN NOT NULL, 
    anonymized_summary_allowed BOOLEAN NOT NULL, 
    consent_snapshot JSON NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(student_user_id) REFERENCES users (id)
);

CREATE INDEX ix_portfolio_permissions_project_id ON portfolio_permissions (project_id);

CREATE INDEX ix_portfolio_permissions_student_user_id ON portfolio_permissions (student_user_id);

CREATE TABLE project_scope_versions (
    project_id UUID NOT NULL, 
    version INTEGER NOT NULL, 
    status VARCHAR(32) NOT NULL, 
    snapshot JSON NOT NULL, 
    immutable_at TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    UNIQUE (project_id, version)
);

CREATE INDEX ix_project_scope_versions_project_id ON project_scope_versions (project_id);

CREATE TABLE project_transitions (
    project_id UUID NOT NULL, 
    actor_id UUID NOT NULL, 
    previous_state VARCHAR(64) NOT NULL, 
    new_state VARCHAR(64) NOT NULL, 
    reason TEXT NOT NULL, 
    correlation_id UUID NOT NULL, 
    idempotency_key VARCHAR(128) NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(actor_id) REFERENCES users (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    UNIQUE (idempotency_key)
);

CREATE INDEX ix_project_transitions_actor_id ON project_transitions (actor_id);

CREATE INDEX ix_project_transitions_correlation_id ON project_transitions (correlation_id);

CREATE INDEX ix_project_transitions_project_id ON project_transitions (project_id);

CREATE TABLE reputation_events (
    student_user_id UUID NOT NULL, 
    project_id UUID NOT NULL, 
    dimension VARCHAR(40) NOT NULL, 
    value INTEGER NOT NULL, 
    evidence_type VARCHAR(50) NOT NULL, 
    evidence_id UUID NOT NULL, 
    approved_by_id UUID NOT NULL, 
    reversed_at TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(approved_by_id) REFERENCES users (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(student_user_id) REFERENCES users (id)
);

CREATE INDEX ix_reputation_events_project_id ON reputation_events (project_id);

CREATE INDEX ix_reputation_events_student_user_id ON reputation_events (student_user_id);

CREATE TABLE scope_change_requests (
    project_id UUID NOT NULL, 
    requested_by_id UUID NOT NULL, 
    request_text TEXT NOT NULL, 
    classification VARCHAR(40) NOT NULL, 
    evidence JSON NOT NULL, 
    classified_by_id UUID, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(classified_by_id) REFERENCES users (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(requested_by_id) REFERENCES users (id)
);

CREATE INDEX ix_scope_change_requests_project_id ON scope_change_requests (project_id);

CREATE TABLE student_skills (
    student_profile_id UUID NOT NULL, 
    skill_id UUID NOT NULL, 
    proficiency INTEGER NOT NULL, 
    source VARCHAR(32) NOT NULL, 
    evidence_count INTEGER NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(skill_id) REFERENCES skills (id), 
    FOREIGN KEY(student_profile_id) REFERENCES student_profiles (id), 
    UNIQUE (student_profile_id, skill_id)
);

CREATE INDEX ix_student_skills_skill_id ON student_skills (skill_id);

CREATE INDEX ix_student_skills_student_profile_id ON student_skills (student_profile_id);

CREATE TABLE university_enrollments (
    university_id UUID NOT NULL, 
    student_profile_id UUID NOT NULL, 
    consented BOOLEAN NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(student_profile_id) REFERENCES student_profiles (id), 
    FOREIGN KEY(university_id) REFERENCES universities (id)
);

CREATE INDEX ix_university_enrollments_student_profile_id ON university_enrollments (student_profile_id);

CREATE INDEX ix_university_enrollments_university_id ON university_enrollments (university_id);

CREATE TABLE work_logs (
    project_id UUID NOT NULL, 
    student_user_id UUID NOT NULL, 
    minutes INTEGER NOT NULL, 
    description TEXT NOT NULL, 
    submitted_at TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(student_user_id) REFERENCES users (id)
);

CREATE INDEX ix_work_logs_project_id ON work_logs (project_id);

CREATE INDEX ix_work_logs_student_user_id ON work_logs (student_user_id);

CREATE TABLE acceptance_criteria (
    scope_version_id UUID NOT NULL, 
    ordinal INTEGER NOT NULL, 
    description TEXT NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(scope_version_id) REFERENCES project_scope_versions (id)
);

CREATE INDEX ix_acceptance_criteria_scope_version_id ON acceptance_criteria (scope_version_id);

CREATE TABLE agent_run_events (
    agent_run_id UUID NOT NULL, 
    event_type VARCHAR(50) NOT NULL, 
    payload JSON NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(agent_run_id) REFERENCES agent_runs (id)
);

CREATE INDEX ix_agent_run_events_agent_run_id ON agent_run_events (agent_run_id);

CREATE TABLE appeal_evidence (
    appeal_id UUID NOT NULL, 
    submitted_by_id UUID NOT NULL, 
    evidence_type VARCHAR(40) NOT NULL, 
    payload JSON NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(appeal_id) REFERENCES appeals (id), 
    FOREIGN KEY(submitted_by_id) REFERENCES users (id)
);

CREATE INDEX ix_appeal_evidence_appeal_id ON appeal_evidence (appeal_id);

CREATE TABLE client_decisions (
    project_id UUID NOT NULL, 
    deliverable_id UUID, 
    actor_id UUID NOT NULL, 
    decision VARCHAR(30) NOT NULL, 
    reason TEXT NOT NULL, 
    revision_round INTEGER NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(actor_id) REFERENCES users (id), 
    FOREIGN KEY(deliverable_id) REFERENCES deliverables (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE INDEX ix_client_decisions_project_id ON client_decisions (project_id);

CREATE TABLE credential_evidence (
    credential_id UUID NOT NULL, 
    evidence_type VARCHAR(40) NOT NULL, 
    evidence_id UUID NOT NULL, 
    public_payload JSON NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(credential_id) REFERENCES credentials (id)
);

CREATE INDEX ix_credential_evidence_credential_id ON credential_evidence (credential_id);

CREATE TABLE deliverable_artifacts (
    deliverable_id UUID NOT NULL, 
    kind VARCHAR(30) NOT NULL, 
    uri TEXT NOT NULL, 
    commit_sha VARCHAR(64), 
    content_hash VARCHAR(64) NOT NULL, 
    scan_status VARCHAR(30) NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(deliverable_id) REFERENCES deliverables (id)
);

CREATE INDEX ix_deliverable_artifacts_deliverable_id ON deliverable_artifacts (deliverable_id);

CREATE TABLE lead_reviews (
    project_id UUID NOT NULL, 
    deliverable_id UUID, 
    lead_user_id UUID NOT NULL, 
    review_type VARCHAR(30) NOT NULL, 
    recommendation VARCHAR(30) NOT NULL, 
    findings JSON NOT NULL, 
    conflict_declared BOOLEAN NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(deliverable_id) REFERENCES deliverables (id), 
    FOREIGN KEY(lead_user_id) REFERENCES users (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE INDEX ix_lead_reviews_lead_user_id ON lead_reviews (lead_user_id);

CREATE INDEX ix_lead_reviews_project_id ON lead_reviews (project_id);

CREATE TABLE payouts (
    allocation_id UUID NOT NULL, 
    provider_reference VARCHAR(255), 
    status VARCHAR(30) NOT NULL, 
    failure_reason TEXT, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(allocation_id) REFERENCES payout_allocations (id)
);

CREATE INDEX ix_payouts_allocation_id ON payouts (allocation_id);

CREATE TABLE project_assignments (
    project_id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    role VARCHAR(50) NOT NULL, 
    offer_id UUID NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(offer_id) REFERENCES assignment_offers (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(user_id) REFERENCES users (id), 
    UNIQUE (offer_id)
);

CREATE INDEX ix_project_assignments_project_id ON project_assignments (project_id);

CREATE INDEX ix_project_assignments_user_id ON project_assignments (user_id);

CREATE TABLE quotes (
    project_id UUID NOT NULL, 
    scope_version_id UUID NOT NULL, 
    version INTEGER NOT NULL, 
    currency VARCHAR(3) NOT NULL, 
    low_minor INTEGER NOT NULL, 
    base_minor INTEGER NOT NULL, 
    high_minor INTEGER NOT NULL, 
    revision_rounds INTEGER NOT NULL, 
    formula_version VARCHAR(40) NOT NULL, 
    status VARCHAR(32) NOT NULL, 
    calculation_inputs JSON NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(scope_version_id) REFERENCES project_scope_versions (id), 
    UNIQUE (project_id, version)
);

CREATE INDEX ix_quotes_project_id ON quotes (project_id);

CREATE TABLE staffing_runs (
    project_id UUID NOT NULL, 
    scope_version_id UUID NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    weights_version VARCHAR(40) NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id), 
    FOREIGN KEY(scope_version_id) REFERENCES project_scope_versions (id)
);

CREATE INDEX ix_staffing_runs_project_id ON staffing_runs (project_id);

CREATE TABLE tasks (
    project_id UUID NOT NULL, 
    milestone_id UUID, 
    assignee_id UUID, 
    title VARCHAR(200) NOT NULL, 
    definition_of_done TEXT NOT NULL, 
    state VARCHAR(30) NOT NULL, 
    dependency_ids JSON NOT NULL, 
    estimate_hours INTEGER NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(assignee_id) REFERENCES users (id), 
    FOREIGN KEY(milestone_id) REFERENCES milestones (id), 
    FOREIGN KEY(project_id) REFERENCES projects (id)
);

CREATE INDEX ix_tasks_assignee_id ON tasks (assignee_id);

CREATE INDEX ix_tasks_milestone_id ON tasks (milestone_id);

CREATE INDEX ix_tasks_project_id ON tasks (project_id);

CREATE INDEX ix_tasks_project_state ON tasks (project_id, state);

CREATE TABLE qa_reviews (
    deliverable_id UUID NOT NULL, 
    artifact_id UUID NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    recommendation VARCHAR(30) NOT NULL, 
    deterministic_evidence JSON NOT NULL, 
    agent_run_id UUID, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(agent_run_id) REFERENCES agent_runs (id), 
    FOREIGN KEY(artifact_id) REFERENCES deliverable_artifacts (id), 
    FOREIGN KEY(deliverable_id) REFERENCES deliverables (id)
);

CREATE INDEX ix_qa_reviews_deliverable_id ON qa_reviews (deliverable_id);

CREATE TABLE quote_line_items (
    quote_id UUID NOT NULL, 
    kind VARCHAR(40) NOT NULL, 
    description VARCHAR(200) NOT NULL, 
    amount_minor INTEGER NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(quote_id) REFERENCES quotes (id)
);

CREATE INDEX ix_quote_line_items_quote_id ON quote_line_items (quote_id);

CREATE TABLE staffing_candidates (
    staffing_run_id UUID NOT NULL, 
    student_profile_id UUID NOT NULL, 
    score_basis_points INTEGER NOT NULL, 
    confidence VARCHAR(20) NOT NULL, 
    components JSON NOT NULL, 
    explanation TEXT NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(staffing_run_id) REFERENCES staffing_runs (id), 
    FOREIGN KEY(student_profile_id) REFERENCES student_profiles (id)
);

CREATE INDEX ix_staffing_candidates_staffing_run_id ON staffing_candidates (staffing_run_id);

CREATE INDEX ix_staffing_candidates_student_profile_id ON staffing_candidates (student_profile_id);

CREATE TABLE qa_findings (
    qa_review_id UUID NOT NULL, 
    criterion_id UUID, 
    source VARCHAR(30) NOT NULL, 
    severity VARCHAR(20) NOT NULL, 
    summary TEXT NOT NULL, 
    evidence JSON NOT NULL, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(criterion_id) REFERENCES acceptance_criteria (id), 
    FOREIGN KEY(qa_review_id) REFERENCES qa_reviews (id)
);

CREATE INDEX ix_qa_findings_qa_review_id ON qa_findings (qa_review_id);

INSERT INTO alembic_version (version_num) VALUES ('fdeefd043d61') RETURNING alembic_version.version_num;

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

