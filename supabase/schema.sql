-- Enable extensions
create extension if not exists vector;

-- Profiles
create table public.profiles (
  id uuid references auth.users primary key,
  email text,
  points float default 5,
  plan text default 'free'
);

-- Transactions
create table public.transactions (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users,
  amount integer,
  points_added float,
  reference text unique,
  status text default 'pending',
  created_at timestamp default now()
);

-- Projects
create table public.projects (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users,
  name text,
  points_used float default 0,
  status text default 'active',
  created_at timestamp default now()
);

-- Messages
create table public.messages (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users,
  project_id uuid references projects,
  sender text,
  content text,
  created_at timestamp default now()
);

-- RLS
alter table profiles enable row level security;
create policy "Users can read own profile" on profiles for select using (auth.uid() = id);
create policy "Users can update own profile" on profiles for update using (auth.uid() = id);

alter table transactions enable row level security;
create policy "Users can read own transactions" on transactions for select using (auth.uid() = user_id);
create policy "Users can insert own transactions" on transactions for insert with check (auth.uid() = user_id);

alter table projects enable row level security;
create policy "Users can read own projects" on projects for select using (auth.uid() = user_id);
create policy "Users can insert own projects" on projects for insert with check (auth.uid() = user_id);

alter table messages enable row level security;
create policy "Users can read own messages" on messages for select using (auth.uid() = user_id);
create policy "Users can insert own messages" on messages for insert with check (auth.uid() = user_id);

-- Functions
create or replace function add_points(user_id uuid, points float)
returns void language plpgsql as $$
begin
  update profiles set points = points + add_points.points where id = user_id;
end;
$$;

create or replace function deduct_point(user_id uuid)
returns void language plpgsql as $$
begin
  update profiles set points = points - 1 where id = user_id;
end;
$$;

-- Trigger to create profile on signup
create or replace function public.handle_new_user()
returns trigger language plpgsql as $$
begin
  insert into public.profiles (id, email, points)
  values (new.id, new.email, 5);
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
