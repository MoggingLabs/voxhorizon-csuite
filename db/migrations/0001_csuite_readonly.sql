-- 0001_csuite_readonly.sql
-- C-Suite read-only DB role for the Data Brain MCP (security control C3).
-- SELECT-only by construction: no INSERT/UPDATE/DELETE/TRUNCATE/DDL is granted.
-- The role password is set out of band by bootstrap-csuite.sh (a runtime secret,
-- never committed). Forward-only and idempotent: safe to re-apply.

do $$
begin
  if not exists (select from pg_roles where rolname = 'csuite_readonly') then
    create role csuite_readonly login;
  end if;
end
$$;

grant connect on database postgres to csuite_readonly;
grant usage on schema public to csuite_readonly;
grant select on all tables in schema public to csuite_readonly;
alter default privileges in schema public grant select on tables to csuite_readonly;
