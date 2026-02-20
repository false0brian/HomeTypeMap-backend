CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS locations (
  id BIGINT PRIMARY KEY,
  latitude NUMERIC(10,7) NOT NULL,
  longitude NUMERIC(10,7) NOT NULL,
  admin_dong VARCHAR(120) NOT NULL,
  legal_dong VARCHAR(120) NOT NULL,
  address VARCHAR(300) NOT NULL,
  point GEOGRAPHY(POINT,4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_locations_point ON locations USING GIST (point);
CREATE INDEX IF NOT EXISTS ix_locations_address ON locations (address);

CREATE TABLE IF NOT EXISTS complexes (
  id BIGINT PRIMARY KEY,
  location_id BIGINT NOT NULL REFERENCES locations(id) ON DELETE RESTRICT,
  name VARCHAR(200) NOT NULL,
  address VARCHAR(300) NOT NULL,
  built_year INT,
  household_count INT,
  centroid_latitude NUMERIC(10,7) NOT NULL,
  centroid_longitude NUMERIC(10,7) NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_complexes_name ON complexes (name);
CREATE INDEX IF NOT EXISTS ix_complexes_address ON complexes (address);

CREATE TABLE IF NOT EXISTS unit_types (
  id BIGINT PRIMARY KEY,
  complex_id BIGINT NOT NULL REFERENCES complexes(id) ON DELETE CASCADE,
  exclusive_area_m2 NUMERIC(7,2) NOT NULL,
  supply_area_m2 NUMERIC(7,2),
  type_code VARCHAR(20),
  room_count INT,
  bathroom_count INT,
  structure_keyword VARCHAR(50),
  CONSTRAINT uq_unit_types_complex_area_type UNIQUE (complex_id, exclusive_area_m2, type_code)
);
CREATE INDEX IF NOT EXISTS ix_unit_types_complex_id ON unit_types (complex_id);
CREATE INDEX IF NOT EXISTS ix_unit_types_exclusive_area_m2 ON unit_types (exclusive_area_m2);

CREATE TABLE IF NOT EXISTS vendors (
  id BIGINT PRIMARY KEY,
  name VARCHAR(160) NOT NULL UNIQUE,
  region VARCHAR(120),
  rating NUMERIC(2,1),
  contact_url VARCHAR(300)
);

CREATE TABLE IF NOT EXISTS portfolios (
  id BIGINT PRIMARY KEY,
  complex_id BIGINT NOT NULL REFERENCES complexes(id) ON DELETE RESTRICT,
  unit_type_id BIGINT NOT NULL REFERENCES unit_types(id) ON DELETE RESTRICT,
  vendor_id BIGINT REFERENCES vendors(id) ON DELETE SET NULL,
  title VARCHAR(220) NOT NULL,
  before_image_url VARCHAR(500),
  after_image_url VARCHAR(500),
  work_scope VARCHAR(80) NOT NULL,
  style VARCHAR(80) NOT NULL,
  budget_min_krw INT,
  budget_max_krw INT,
  duration_days INT,
  tags TEXT,
  summary TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'draft',
  published_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT ck_portfolios_budget_order
    CHECK (budget_min_krw IS NULL OR budget_max_krw IS NULL OR budget_min_krw <= budget_max_krw)
);
CREATE INDEX IF NOT EXISTS ix_portfolios_complex_unit ON portfolios (complex_id, unit_type_id);
CREATE INDEX IF NOT EXISTS ix_portfolios_style ON portfolios (style);
CREATE INDEX IF NOT EXISTS ix_portfolios_work_scope ON portfolios (work_scope);
CREATE INDEX IF NOT EXISTS ix_portfolios_budget_range ON portfolios (budget_min_krw, budget_max_krw);
CREATE INDEX IF NOT EXISTS ix_portfolios_status ON portfolios (status);

CREATE TABLE IF NOT EXISTS blog_posts (
  id BIGINT PRIMARY KEY,
  vendor_id BIGINT REFERENCES vendors(id) ON DELETE SET NULL,
  title VARCHAR(220) NOT NULL,
  slug VARCHAR(140) NOT NULL UNIQUE,
  excerpt VARCHAR(500),
  content TEXT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'draft',
  published_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_blog_posts_vendor_id ON blog_posts (vendor_id);
CREATE INDEX IF NOT EXISTS ix_blog_posts_status ON blog_posts (status);
CREATE INDEX IF NOT EXISTS ix_blog_posts_published_at ON blog_posts (published_at);

CREATE TABLE IF NOT EXISTS floor_plans (
  id BIGINT PRIMARY KEY,
  unit_type_id BIGINT NOT NULL REFERENCES unit_types(id) ON DELETE CASCADE,
  image_url VARCHAR(500) NOT NULL,
  structure_tags TEXT,
  embedding TEXT
);

CREATE TABLE IF NOT EXISTS user_favorites (
  id BIGINT PRIMARY KEY,
  user_key VARCHAR(80) NOT NULL,
  portfolio_id BIGINT NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_user_favorites_user_portfolio UNIQUE (user_key, portfolio_id)
);
CREATE INDEX IF NOT EXISTS ix_user_favorites_user_key ON user_favorites (user_key);

CREATE TABLE IF NOT EXISTS quote_requests (
  id BIGINT PRIMARY KEY,
  user_key VARCHAR(80) NOT NULL,
  portfolio_id BIGINT REFERENCES portfolios(id) ON DELETE SET NULL,
  vendor_id BIGINT REFERENCES vendors(id) ON DELETE SET NULL,
  preferred_date DATE,
  message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
