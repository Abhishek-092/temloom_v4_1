-- 002_roles_and_permissions.sql
-- Logical Database Role Separation for PostgreSQL 16 Deployment
-- 1. temloom_core_rw: Full read/write on operational telemetry & predictions (zero read on ground_truth_* from feature extractor)
-- 2. temloom_copilot_ro: Strictly SELECT-only on structured incident views and rag_knowledge_chunks
-- 3. temloom_audit_append: Strictly INSERT/SELECT on audit_log_chain (UPDATE/DELETE revoked)

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'temloom_core_rw') THEN
        CREATE ROLE temloom_core_rw LOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'temloom_copilot_ro') THEN
        CREATE ROLE temloom_copilot_ro LOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'temloom_audit_append') THEN
        CREATE ROLE temloom_audit_append LOGIN;
    END IF;
END
$$;

GRANT SELECT ON rag_knowledge_chunks, prediction_outputs, rca_outputs, remediation_outcomes TO temloom_copilot_ro;
REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM temloom_copilot_ro;

GRANT SELECT, INSERT ON audit_log_chain TO temloom_audit_append;
REVOKE UPDATE, DELETE ON audit_log_chain FROM temloom_audit_append, temloom_core_rw;
