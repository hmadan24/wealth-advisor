-- Wealth Advisor - Supabase Database Schema
-- Run this in Supabase SQL Editor to create tables

-- Users table
CREATE TABLE IF NOT EXISTS users (
    phone VARCHAR(15) PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    supabase_uid VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for supabase_uid lookups
CREATE INDEX IF NOT EXISTS idx_users_supabase_uid ON users(supabase_uid);

-- Portfolios table
CREATE TABLE IF NOT EXISTS portfolios (
    id VARCHAR(36) PRIMARY KEY,
    phone VARCHAR(15) NOT NULL,
    filename VARCHAR(255),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    portfolio_data TEXT  -- JSON stored as text
);

-- Create index for user portfolio lookups
CREATE INDEX IF NOT EXISTS idx_portfolios_phone ON portfolios(phone);

-- Enable Row Level Security (optional, for Supabase Auth integration)
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;

-- Example RLS policies (uncomment if using Supabase Auth)
-- CREATE POLICY "Users can read own data" ON users
--     FOR SELECT USING (auth.uid()::text = supabase_uid);

-- CREATE POLICY "Users can read own portfolios" ON portfolios
--     FOR ALL USING (phone = (SELECT phone FROM users WHERE supabase_uid = auth.uid()::text));

