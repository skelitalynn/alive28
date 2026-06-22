-- Run once against an existing SQLite database before starting the F-005 code.
-- New proofapproval and proofcompensation tables are created by SQLModel create_all.

ALTER TABLE dailylog
ADD COLUMN proof_status VARCHAR(24) NOT NULL DEFAULT 'ACTIVE';

ALTER TABLE dailylog
ADD COLUMN effective_proof_hash VARCHAR(66);

CREATE INDEX IF NOT EXISTS ix_dailylog_proof_status
ON dailylog (proof_status);
