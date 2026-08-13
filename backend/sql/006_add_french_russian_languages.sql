-- Enable French and Russian translations on an existing database.
begin;

alter table menu_category_translations
    drop constraint if exists ck_menu_category_translations_language;

alter table menu_category_translations
    add constraint ck_menu_category_translations_language
    check (language_code in ('el', 'en', 'de', 'it', 'sv', 'fr', 'ru', 'he'));

alter table menu_item_translations
    drop constraint if exists ck_menu_item_translations_language;

alter table menu_item_translations
    add constraint ck_menu_item_translations_language
    check (language_code in ('el', 'en', 'de', 'it', 'sv', 'fr', 'ru', 'he'));

commit;
