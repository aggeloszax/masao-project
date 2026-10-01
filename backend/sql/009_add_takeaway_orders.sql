-- Take-away orders placed from the guest menu.
--
-- Η παραγγελία αποθηκεύεται ΠΡΙΝ σταλεί το email, ώστε μια αποτυχία στον
-- email provider να μη χάνει την παραγγελία. Το notified_at δείχνει αν η
-- ειδοποίηση έφυγε· το email_error κρατά τον λόγο αποτυχίας.

begin;

create table if not exists takeaway_orders (
    id uuid primary key default gen_random_uuid(),
    customer_name varchar(120) not null check (length(trim(customer_name)) > 0),
    customer_phone varchar(40) not null check (length(trim(customer_phone)) > 0),
    pickup_slot varchar(16) not null check (pickup_slot in ('asap', 'in_30', 'in_60')),
    language_code varchar(8) not null,
    -- Snapshot των γραμμών τη στιγμή της παραγγελίας: οι τιμές του μενού
    -- αλλάζουν, η παραγγελία όχι.
    items jsonb not null,
    total numeric(10, 2) not null check (total >= 0),
    notified_at timestamp with time zone,
    email_error text,
    created_at timestamp with time zone not null default now()
);

create index if not exists idx_takeaway_orders_created_at
    on takeaway_orders(created_at desc);

-- Παραγγελίες που δεν ειδοποιήθηκαν: η ουρά που πρέπει να κοιτάει κάποιος.
create index if not exists idx_takeaway_orders_unnotified
    on takeaway_orders(created_at desc)
    where notified_at is null;

commit;
