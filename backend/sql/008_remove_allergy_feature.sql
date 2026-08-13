-- Remove the retired allergy profile and menu-allergen feature.
-- Idempotent for both upgraded and clean databases.

begin;

drop table if exists customer_allergy_profiles;

drop index if exists idx_menu_items_allergens_gin;

alter table if exists menu_items
    drop constraint if exists ck_menu_items_allergens_valid;

alter table if exists menu_items
    drop column if exists allergens;

commit;
