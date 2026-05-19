-- Выполните в Supabase: SQL Editor → New query → Run
-- Бесплатный тариф Supabase Auth: email, magic link, (SMS — через Twilio trial)

create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email text,
  phone text,
  paid boolean not null default false,
  payment_status text not null default 'none'
    check (payment_status in ('none', 'pending', 'paid')),
  payment_code text,
  paid_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

create policy "profiles_select_own"
  on public.profiles for select
  using (auth.uid() = id);

create policy "profiles_update_own"
  on public.profiles for update
  using (auth.uid() = id)
  with check (
    auth.uid() = id
    and paid is not distinct from (
      select p.paid from public.profiles as p where p.id = auth.uid()
    )
  );

create policy "profiles_insert_own"
  on public.profiles for insert
  with check (auth.uid() = id);

-- Триггер: профиль при регистрации
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, email, phone, payment_code)
  values (
    new.id,
    new.email,
    new.phone,
    'PAY-' || upper(substr(replace(new.id::text, '-', ''), 1, 8))
  );
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- Админ: подтверждение оплаты (вызов из admin с service_role или вручную в Table Editor)
create or replace function public.admin_confirm_payment(target_user_id uuid)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.profiles
  set paid = true,
      payment_status = 'paid',
      paid_at = now(),
      updated_at = now()
  where id = target_user_id;
end;
$$;
