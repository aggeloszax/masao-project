-- Pseudonymize existing chat device identifiers and support retention cleanup.
-- Apply after 001_init_masao_schema.sql on existing installations.

begin;

update chat_sessions
set device_id = encode(digest(device_id, 'sha256'), 'hex')
where device_id !~ '^[0-9a-f]{64}$';

create index if not exists idx_chat_sessions_created_at
    on chat_sessions(created_at);

commit;
