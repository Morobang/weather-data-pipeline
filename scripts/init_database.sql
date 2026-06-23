-- ============================================================
-- INITIALIZE DATABASE
-- Creates the three schemas for the medallion architecture
-- Run this first before any other SQL file
-- ============================================================

-- BRONZE — raw data, exactly as it came from the API
-- Nothing is cleaned or transformed here
CREATE SCHEMA IF NOT EXISTS bronze;

-- SILVER — cleaned, typed, exploded
-- JSON is unpacked into proper columns with correct data types
CREATE SCHEMA IF NOT EXISTS silver;

-- GOLD — aggregated views
-- Business-ready summaries built on top of silver
CREATE SCHEMA IF NOT EXISTS gold;