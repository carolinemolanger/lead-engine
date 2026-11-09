-- =========================================================
-- Lead Engine: tabelas do banco
-- Linhas que começam com -- são comentários (o banco ignora)
-- =========================================================

-- Vendedores
CREATE TABLE IF NOT EXISTS sales_reps (
    rep_id   SERIAL PRIMARY KEY,
    name     TEXT NOT NULL,
    email    TEXT NOT NULL UNIQUE,
    team     TEXT NOT NULL CHECK (team IN ('enterprise', 'smb')),
    active   BOOLEAN NOT NULL DEFAULT TRUE
);

-- Leads
CREATE TABLE IF NOT EXISTS leads (
    lead_id               BIGINT PRIMARY KEY,
    prospect_id           TEXT,
    full_name             TEXT,
    email                 TEXT,
    phone                 TEXT,
    lead_origin           TEXT,
    lead_source           TEXT,
    last_activity         TEXT,
    occupation            TEXT,
    specialization        TEXT,
    city                  TEXT,
    total_visits          NUMERIC,
    time_on_site_sec      NUMERIC,
    pages_per_visit       NUMERIC,
    do_not_email          BOOLEAN DEFAULT FALSE,
    do_not_call           BOOLEAN DEFAULT FALSE,
    converted_historical  SMALLINT,
    lead_score            SMALLINT,
    score_band            TEXT,
    status                TEXT NOT NULL DEFAULT 'novo'
                          CHECK (status IN ('novo','enviado','em_contato','ganho','perdido')),
    assigned_rep_id       INT REFERENCES sales_reps(rep_id),
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    dispatched_at         TIMESTAMPTZ,
    closed_at             TIMESTAMPTZ
);

-- Registro de cada envio feito pelo n8n
CREATE TABLE IF NOT EXISTS lead_dispatches (
    dispatch_id  BIGSERIAL PRIMARY KEY,
    lead_id      BIGINT NOT NULL REFERENCES leads(lead_id),
    rep_id       INT NOT NULL REFERENCES sales_reps(rep_id),
    channel      TEXT NOT NULL DEFAULT 'email',
    sent_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Vendedores de exemplo (fictícios)
INSERT INTO sales_reps (name, email, team) VALUES
    ('Ana Souza',      'ana.souza@exemplo.com',      'enterprise'),
    ('Bruno Lima',     'bruno.lima@exemplo.com',     'enterprise'),
    ('Carla Mendes',   'carla.mendes@exemplo.com',   'smb'),
    ('Diego Ferreira', 'diego.ferreira@exemplo.com', 'smb')
ON CONFLICT (email) DO NOTHING;