-- Add Hebrew ('he') language support to an existing Supabase/PostgreSQL schema.
-- Run this on databases created before Hebrew was (re)introduced — including
-- databases where 003_remove_hebrew_translations.sql was applied.
-- Afterwards, re-run 002_seed_full_menu_from_frontend.sql to load the Hebrew rows.

begin;

alter table menu_category_translations
    drop constraint if exists ck_menu_category_translations_language;

alter table menu_category_translations
    add constraint ck_menu_category_translations_language
    check (language_code in ('el', 'en', 'de', 'it', 'sv', 'he'));

alter table menu_item_translations
    drop constraint if exists ck_menu_item_translations_language;

alter table menu_item_translations
    add constraint ck_menu_item_translations_language
    check (language_code in ('el', 'en', 'de', 'it', 'sv', 'he'));

commit;
