create table if not exists engine_events (
  id bigserial primary key,
  ts timestamptz default now(),
  kind text not null,
  entity_type text,
  entity_id text,
  platform text,
  payload jsonb not null,
  severity text,
  correlation_id text
);

create table if not exists recommendations (
  id bigserial primary key,
  created_at timestamptz default now(),
  entity_type text,
  entity_id text,
  action text,
  from_entity text,
  to_entity text,
  delta_budget numeric,
  confidence numeric,
  rationale text,
  status text default 'pending',
  metadata jsonb
);

create table if not exists executions (
  id bigserial primary key,
  executed_at timestamptz default now(),
  recommendation_id bigint references recommendations(id),
  platform text,
  request jsonb,
  response jsonb,
  success boolean,
  error text
);

create table if not exists outcome_feedback (
  id bigserial primary key,
  recorded_at timestamptz default now(),
  execution_id bigint references executions(id),
  metric text,
  pre_value numeric,
  post_value numeric,
  uplift numeric,
  window_hours integer,
  notes text
);

create index if not exists idx_events_ts on engine_events(ts desc);
create index if not exists idx_events_entity on engine_events(entity_type, entity_id);
create index if not exists idx_recs_status on recommendations(status);
