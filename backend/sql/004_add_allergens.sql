-- Allergy alerts: allergens per menu item + customer allergy profiles.
--
-- Οι κωδικοί αλλεργιογόνων ακολουθούν τα 14 της ΕΕ (Annex II, Reg. 1169/2011)
-- και πρέπει να ταιριάζουν με το api/services/allergens.py.
--
-- ΠΡΟΣΟΧΗ: το seed στο τέλος είναι best effort από τις περιγραφές συστατικών.
-- Το εστιατόριο ΠΡΕΠΕΙ να επαληθεύσει τα allergens κάθε πιάτου μέσω των
-- admin endpoints πριν βασιστεί κανείς στα alerts. Άδεια λίστα σημαίνει
-- "μη αξιολογημένο", όχι "χωρίς αλλεργιογόνα".

alter table menu_items add column if not exists allergens text[] not null default '{}';

create index if not exists idx_menu_items_allergens_gin
    on menu_items using gin(allergens);

-- Data integrity: μόνο κανονικοί κωδικοί επιτρέπονται στη στήλη.
do $$
begin
    if not exists (
        select 1 from pg_constraint where conname = 'ck_menu_items_allergens_valid'
    ) then
        alter table menu_items add constraint ck_menu_items_allergens_valid check (
            allergens <@ array[
                'gluten', 'crustaceans', 'eggs', 'fish', 'peanuts', 'soybeans',
                'milk', 'nuts', 'celery', 'mustard', 'sesame', 'sulphites',
                'lupin', 'molluscs'
            ]::text[]
        );
    end if;
end $$;

-- Ένα προφίλ αλλεργιών ανά ανώνυμη συσκευή (ίδιο device_id με chat_sessions).
create table if not exists customer_allergy_profiles (
    id serial primary key,
    device_id varchar(128) not null unique,
    allergens text[] not null default '{}',
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now(),
    constraint ck_customer_allergy_profiles_valid check (
        allergens <@ array[
            'gluten', 'crustaceans', 'eggs', 'fish', 'peanuts', 'soybeans',
            'milk', 'nuts', 'celery', 'mustard', 'sesame', 'sulphites',
            'lupin', 'molluscs'
        ]::text[]
    )
);

-- ---------------------------------------------------------------------------
-- Best-effort seed από τα αγγλικά ονόματα/περιγραφές συστατικών.
-- Κάθε update είναι idempotent (προσθέτει τον κωδικό μόνο αν λείπει).
-- ---------------------------------------------------------------------------

update menu_items
set allergens = array_append(allergens, 'crustaceans')
where not ('crustaceans' = any(allergens))
  and (name || ' ' || description) ~* '\m(shrimp|shrimps|crab|prawn|prawns|lobster|kanimi)\M';

-- kanimi (surimi) είναι επεξεργασμένο ψάρι· masago/tobico/ikura/caviar είναι αυγοτάραχο.
update menu_items
set allergens = array_append(allergens, 'fish')
where not ('fish' = any(allergens))
  and (name || ' ' || description) ~* '\m(salmon|tuna|sea bass|suzuki|eel|unagi|kanimi|masago|tobico|ikura|caviar|sashimi|anchov)\M';

-- Οι mayo και το tempura/brioche περιέχουν τυπικά αυγό.
update menu_items
set allergens = array_append(allergens, 'eggs')
where not ('eggs' = any(allergens))
  and (name || ' ' || description) ~* '\m(mayo|mayonnaise|egg|eggs|tempura|brioche)\M';

update menu_items
set allergens = array_append(allergens, 'milk')
where not ('milk' = any(allergens))
  and (name || ' ' || description) ~* '\m(cream|cheese|parmesan|cheddar|feta|butter|mascarpone|tiramisu|cheesecake|fondant|milk|yogurt)\M';

-- Σιτάρι σε noodles/bao/tempura/σάλτσες σόγιας και στα κλασικά desserts.
update menu_items
set allergens = array_append(allergens, 'gluten')
where not ('gluten' = any(allergens))
  and (name || ' ' || description) ~* '\m(noodles?|udon|brioche|bun|buns|bao|tempura|panko|dumplings?|gyoza|wonton|spring rolls?|teriyaki|unagi|hoisin|katsu|fondant|cheesecake|tiramisu|soy sauce)\M';

update menu_items
set allergens = array_append(allergens, 'soybeans')
where not ('soybeans' = any(allergens))
  and (name || ' ' || description) ~* '\m(soy|edamame|hoisin|teriyaki|unagi|miso|tofu|ponzu)\M';

update menu_items
set allergens = array_append(allergens, 'sesame')
where not ('sesame' = any(allergens))
  and (name || ' ' || description) ~* '\m(sesame|tahini|togarashi)\M';

update menu_items
set allergens = array_append(allergens, 'nuts')
where not ('nuts' = any(allergens))
  and (name || ' ' || description) ~* '\m(cashew|pistachio|almonds?|walnuts?|hazelnuts?|nuts)\M';

update menu_items
set allergens = array_append(allergens, 'peanuts')
where not ('peanuts' = any(allergens))
  and (name || ' ' || description) ~* '\m(peanuts?)\M';

update menu_items
set allergens = array_append(allergens, 'mustard')
where not ('mustard' = any(allergens))
  and (name || ' ' || description) ~* '\m(mustard)\M';

update menu_items
set allergens = array_append(allergens, 'celery')
where not ('celery' = any(allergens))
  and (name || ' ' || description) ~* '\m(celery)\M';

update menu_items
set allergens = array_append(allergens, 'molluscs')
where not ('molluscs' = any(allergens))
  and (name || ' ' || description) ~* '\m(octopus|squid|calamari|oysters?|mussels?|scallops?)\M';

-- Κρασιά, αφρώδη και ciders περιέχουν θειώδη· οι μπύρες γλουτένη (κριθάρι).
update menu_items mi
set allergens = array_append(mi.allergens, 'sulphites')
from menu_categories mc
where mc.id = mi.category_id
  and mc.name in ('White Wines', 'Rose Wines', 'Red Wines', 'Champagne & Sparkling', 'Ciders')
  and not ('sulphites' = any(mi.allergens));

update menu_items mi
set allergens = array_append(mi.allergens, 'gluten')
from menu_categories mc
where mc.id = mi.category_id
  and mc.name = 'Beers'
  and not ('gluten' = any(mi.allergens));
