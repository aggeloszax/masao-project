-- Retired migration.
--
-- The allergy profile and menu-allergen feature was removed before production
-- use. This file remains as an intentional no-op so existing migration order
-- and deployment records stay stable. Migration 008 removes the legacy schema
-- from databases where an older version of this migration already ran.

select 1;
