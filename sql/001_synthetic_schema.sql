-- PostgreSQL-compatible TASK-001 schema. All rows generated for this schema are synthetic.
CREATE TABLE customer (
    cif text PRIMARY KEY,
    customer_name text NOT NULL,
    segment text NOT NULL CHECK (segment IN ('RED','ORANGE','YELLOW','GREEN')),
    heatmap text NOT NULL CHECK (heatmap IN ('RED','AMBER','GREEN')),
    created_at timestamptz NOT NULL
);

CREATE TABLE loan_account (
    account_id text PRIMARY KEY,
    cif text NOT NULL REFERENCES customer(cif),
    product_type text NOT NULL,
    outstanding_amount numeric(18,2) NOT NULL CHECK (outstanding_amount >= 0),
    overdue_amount numeric(18,2) NOT NULL CHECK (overdue_amount >= 0 AND overdue_amount <= outstanding_amount),
    dpd integer NOT NULL CHECK (dpd >= 0),
    due_amount numeric(18,2) NOT NULL CHECK (due_amount >= 0),
    due_date date NOT NULL,
    status text NOT NULL
);

CREATE TABLE collection_assignment (
    id text PRIMARY KEY,
    cif text NOT NULL REFERENCES customer(cif),
    base_route text NOT NULL CHECK (base_route IN ('CALL','CBS','OTHER')),
    challenge_override_route text CHECK (challenge_override_route IN ('CALL','CBS')),
    effective_route text NOT NULL CHECK (effective_route IN ('CALL','CBS','OTHER')),
    assignment_date date NOT NULL
);

CREATE TABLE operation_result (
    id text PRIMARY KEY,
    cif text NOT NULL REFERENCES customer(cif),
    operation_object text, relation text, detail_relation text, operation_address text,
    operation_result text NOT NULL CHECK (operation_result IN ('UTC','PTP','NPTP','RTP','NIN','THIRT','NA')),
    payment_ptp_date date, payment_ptp_number numeric(18,2),
    payment_ptp_ability text CHECK (payment_ptp_ability IN ('CERTAIN','HIGH','MEDIUM','LOW','VERY_LOW')),
    overall_customer_assessment text, overdue_reason text, detail_overdue_reason text,
    debt_solution text, detail_operation_content text,
    is_change_contact_info boolean NOT NULL, is_current_address boolean NOT NULL,
    is_current_phone_number boolean NOT NULL, next_action_date timestamptz,
    next_operation_channel text, new_phone_number text, need_investigation boolean NOT NULL,
    work_status text, income_status text, affected_repayment_source text, proposed_solution text,
    created_at timestamptz NOT NULL, created_by text NOT NULL,
    updated_at timestamptz NOT NULL, updated_by text NOT NULL
);

CREATE TABLE cashflow_transaction (
    transaction_id text PRIMARY KEY,
    cif text NOT NULL REFERENCES customer(cif),
    transaction_date timestamptz NOT NULL,
    direction text NOT NULL CHECK (direction IN ('IN','OUT')),
    amount numeric(18,2) NOT NULL CHECK (amount > 0),
    source_type text NOT NULL CHECK (source_type IN ('SALARY','BUSINESS_INCOME','TRANSFER','DEPOSIT','OTHER')),
    balance_after numeric(18,2) NOT NULL CHECK (balance_after >= 0)
);

CREATE TABLE payment_event (
    payment_id text PRIMARY KEY,
    cif text NOT NULL REFERENCES customer(cif),
    account_id text NOT NULL REFERENCES loan_account(account_id),
    payment_date timestamptz NOT NULL,
    amount numeric(18,2) NOT NULL CHECK (amount > 0),
    payment_type text NOT NULL,
    linked_ptp_id text REFERENCES operation_result(id)
);

CREATE TABLE call_history (
    id text PRIMARY KEY, call_id text NOT NULL, call_time timestamptz NOT NULL,
    end_time timestamptz NOT NULL, employee_name text NOT NULL, extension text NOT NULL,
    call_phone text NOT NULL, relationship text, cif text NOT NULL REFERENCES customer(cif),
    status text NOT NULL CHECK (status IN ('Success','Error SIP','No Answer','Busy')),
    ring_duration integer NOT NULL CHECK (ring_duration >= 0),
    talk_duration integer NOT NULL CHECK (talk_duration >= 0), call_type text NOT NULL,
    record_file text, customer_name text NOT NULL, created_at timestamptz NOT NULL,
    created_by text NOT NULL, updated_at timestamptz NOT NULL, updated_by text NOT NULL,
    request_code text NOT NULL, start_at timestamptz NOT NULL, pbx text NOT NULL,
    end_at timestamptz NOT NULL, destination_name text NOT NULL,
    operation_status text, operation_source text NOT NULL
);

CREATE TABLE golden_scenario_expected (
    scenario_id text PRIMARY KEY, cif text UNIQUE NOT NULL REFERENCES customer(cif),
    hero boolean NOT NULL, input_fixture jsonb NOT NULL, expected_route text,
    expected_treatment text, expected_channel text, expected_timing_class text,
    expected_priority_band text, must_trigger_rule_ids jsonb NOT NULL,
    must_not_trigger_rule_ids jsonb NOT NULL, expected_score_constraints jsonb NOT NULL,
    rationale text NOT NULL
);

CREATE TABLE generation_manifest (
    id integer PRIMARY KEY DEFAULT 1 CHECK (id = 1), seed bigint NOT NULL,
    reference_date date NOT NULL, generator_version text NOT NULL,
    generated_at timestamptz NOT NULL, is_synthetic boolean NOT NULL CHECK (is_synthetic),
    counts jsonb NOT NULL, golden_scenario_count integer NOT NULL,
    hero_scenario_count integer NOT NULL, deterministic_digest text NOT NULL
);

CREATE VIEW customer_recovery_source_features AS
SELECT c.cif, SUM(l.outstanding_amount) AS total_outstanding_cif,
       MAX(l.dpd) AS max_dpd_cif, a.effective_route AS route,
       SUM(l.due_amount) AS current_due_amount
FROM customer c
JOIN loan_account l ON l.cif = c.cif
JOIN collection_assignment a ON a.cif = c.cif
GROUP BY c.cif, a.effective_route;

