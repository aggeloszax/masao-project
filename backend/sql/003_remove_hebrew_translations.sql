-- Remove Hebrew language support from existing Supabase/PostgreSQL schema.
-- Run this after 001_init_masao_schema.sql if an earlier schema allowed 'he'.

begin;

delete from menu_item_translations
where language_code = 'he';

delete from menu_category_translations
where language_code = 'he';

alter table menu_category_translations
    drop constraint if exists ck_menu_category_translations_language;

alter table menu_category_translations
    add constraint ck_menu_category_translations_language
    check (language_code in ('el', 'en', 'de', 'it', 'sv'));

alter table menu_item_translations
    drop constraint if exists ck_menu_item_translations_language;

alter table menu_item_translations
    add constraint ck_menu_item_translations_language
    check (language_code in ('el', 'en', 'de', 'it', 'sv'));

commit;
