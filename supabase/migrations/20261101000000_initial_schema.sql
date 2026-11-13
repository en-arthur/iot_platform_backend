-- Initial Schema Migration for AI IoT Builder
-- Supabase Postgres with Row Level Security (RLS)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- 1. PROFILES (Linked to auth.users)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    full_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Columns written by the onboarding form (app/(auth)/onboarding/page.js).
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS role TEXT;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS target_goal TEXT;

-- =============================================================================
-- 2. PROJECTS
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.projects (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    board_id TEXT NOT NULL,
    interface_type TEXT NOT NULL DEFAULT 'dashboard' CHECK (interface_type IN ('dashboard', 'web app')),
    lifecycle TEXT NOT NULL DEFAULT 'draft' CHECK (lifecycle IN ('draft', 'validated', 'confirmed', 'generated', 'verified', 'deployed')),
    version INTEGER NOT NULL DEFAULT 1,
    deployed_version TEXT DEFAULT 'v1.0',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_projects_user_id ON public.projects(user_id);

-- Latest (editable) specification, persisted on every create/patch/confirm so
-- projects survive backend redeploys.
ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS current_spec JSONB;

-- =============================================================================
-- 3. SPEC VERSIONS (Immutable snapshots of 12-section model)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.spec_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id TEXT NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    spec JSONB NOT NULL,
    author TEXT NOT NULL,
    summary TEXT NOT NULL,
    diff JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(project_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_spec_versions_project ON public.spec_versions(project_id, version_number DESC);

-- =============================================================================
-- 4. PROPOSALS (AI proposed changes waiting for user sign-off)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.proposals (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    summary TEXT NOT NULL,
    changes JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_proposals_project_id ON public.proposals(project_id);

-- =============================================================================
-- 5. GENERATED FILES (Synthesized source code artifacts)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.generated_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id TEXT NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    path TEXT NOT NULL,
    content TEXT,
    storage_path TEXT,
    file_type TEXT NOT NULL,
    is_protected BOOLEAN NOT NULL DEFAULT FALSE,
    checksum TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(project_id, version_number, path)
);

CREATE INDEX IF NOT EXISTS idx_generated_files_project_version ON public.generated_files(project_id, version_number);

-- =============================================================================
-- 6. VERIFICATION RUNS (Sandbox compiler and self-test runs)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.verification_runs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'passed', 'failed')),
    sandbox_provider TEXT NOT NULL DEFAULT 'e2b',
    logs TEXT,
    firmware_binary_url TEXT,
    selftest_results JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_verification_runs_project ON public.verification_runs(project_id);

-- =============================================================================
-- 7. DEVICES (Provisioned hardware units)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.devices (
    id TEXT PRIMARY KEY,
    device_id TEXT,
    project_id TEXT NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    secret_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'offline' CHECK (status IN ('offline', 'online', 'error')),
    last_seen_at TIMESTAMPTZ,
    ip_address TEXT,
    firmware_version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.devices ADD COLUMN IF NOT EXISTS device_id TEXT;
ALTER TABLE public.devices ADD COLUMN IF NOT EXISTS secret_hash TEXT;
ALTER TABLE public.devices ADD COLUMN IF NOT EXISTS project_id TEXT;

-- Sync device_id with id if device_id is null
UPDATE public.devices SET device_id = id WHERE device_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_devices_project_id ON public.devices(project_id);

-- =============================================================================
-- 8. READINGS (Telemetry data ingested via MQTT)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.readings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id TEXT,
    project_id TEXT,
    metric TEXT NOT NULL,
    value NUMERIC NOT NULL,
    unit TEXT,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Ensure columns exist even if readings table was created by an older migration
ALTER TABLE public.readings ADD COLUMN IF NOT EXISTS device_id TEXT;
ALTER TABLE public.readings ADD COLUMN IF NOT EXISTS project_id TEXT;
ALTER TABLE public.readings ADD COLUMN IF NOT EXISTS metric TEXT;
ALTER TABLE public.readings ADD COLUMN IF NOT EXISTS value NUMERIC;
ALTER TABLE public.readings ADD COLUMN IF NOT EXISTS unit TEXT;
ALTER TABLE public.readings ADD COLUMN IF NOT EXISTS recorded_at TIMESTAMPTZ DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_readings_device_recorded ON public.readings(device_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_readings_project_metric ON public.readings(project_id, metric, recorded_at DESC);

-- =============================================================================
-- 9. HARDWARE LIBRARY TABLES
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.library_boards (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    vendor TEXT NOT NULL,
    mcu TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'tested', 'deprecated', 'unverified')),
    specs JSONB NOT NULL,
    pin_map JSONB NOT NULL,
    tested_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.library_peripherals (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    interface TEXT NOT NULL,
    default_address TEXT,
    pins_required JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'tested', 'deprecated', 'unverified')),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.driver_blocks (
    id TEXT PRIMARY KEY,
    peripheral_id TEXT NOT NULL REFERENCES public.library_peripherals(id) ON DELETE CASCADE,
    framework TEXT NOT NULL DEFAULT 'esp-idf',
    header_code TEXT NOT NULL,
    source_code TEXT NOT NULL,
    config_schema JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.patterns (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    template_slots JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'tested',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 10. AUDIT LOG (Tracks confirm, deploy, provision, command actions)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    project_id TEXT REFERENCES public.projects(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_project ON public.audit_log(project_id, created_at DESC);

-- =============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- Rule: The frontend READS from Supabase directly (RLS) but all WRITES go through FastAPI.
-- =============================================================================

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.spec_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.generated_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.verification_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.readings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.library_boards ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.library_peripherals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.driver_blocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patterns ENABLE ROW LEVEL SECURITY;

-- 1. Profiles: Users can select their own profile
DROP POLICY IF EXISTS "Users can read own profile" ON public.profiles;
CREATE POLICY "Users can read own profile" ON public.profiles
    FOR SELECT TO authenticated USING (auth.uid() = id);

-- 1b. Profiles: the onboarding page upserts the user's own row
DROP POLICY IF EXISTS "Users can insert own profile" ON public.profiles;
CREATE POLICY "Users can insert own profile" ON public.profiles
    FOR INSERT TO authenticated WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE TO authenticated USING (auth.uid() = id) WITH CHECK (auth.uid() = id);

-- 2. Projects: Owner can read their projects
DROP POLICY IF EXISTS "Users can read own projects" ON public.projects;
CREATE POLICY "Users can read own projects" ON public.projects
    FOR SELECT TO authenticated USING (auth.uid() = user_id);

-- 3. Spec Versions: Read if owner of project
DROP POLICY IF EXISTS "Users can read own spec versions" ON public.spec_versions;
CREATE POLICY "Users can read own spec versions" ON public.spec_versions
    FOR SELECT TO authenticated USING (
        EXISTS (SELECT 1 FROM public.projects WHERE projects.id = spec_versions.project_id AND projects.user_id = auth.uid())
    );

-- 4. Proposals: Read if owner of project
DROP POLICY IF EXISTS "Users can read own proposals" ON public.proposals;
CREATE POLICY "Users can read own proposals" ON public.proposals
    FOR SELECT TO authenticated USING (
        EXISTS (SELECT 1 FROM public.projects WHERE projects.id = proposals.project_id AND projects.user_id = auth.uid())
    );

-- 5. Generated Files: Read if owner of project
DROP POLICY IF EXISTS "Users can read own generated files" ON public.generated_files;
CREATE POLICY "Users can read own generated files" ON public.generated_files
    FOR SELECT TO authenticated USING (
        EXISTS (SELECT 1 FROM public.projects WHERE projects.id = generated_files.project_id AND projects.user_id = auth.uid())
    );

-- 6. Verification Runs: Read if owner of project
DROP POLICY IF EXISTS "Users can read own verification runs" ON public.verification_runs;
CREATE POLICY "Users can read own verification runs" ON public.verification_runs
    FOR SELECT TO authenticated USING (
        EXISTS (SELECT 1 FROM public.projects WHERE projects.id = verification_runs.project_id AND projects.user_id = auth.uid())
    );

-- 7. Devices: Read if owner of project
DROP POLICY IF EXISTS "Users can read own devices" ON public.devices;
CREATE POLICY "Users can read own devices" ON public.devices
    FOR SELECT TO authenticated USING (
        EXISTS (SELECT 1 FROM public.projects WHERE projects.id = devices.project_id AND projects.user_id = auth.uid())
    );

-- 8. Readings: Read if owner of project
DROP POLICY IF EXISTS "Users can read own readings" ON public.readings;
CREATE POLICY "Users can read own readings" ON public.readings
    FOR SELECT TO authenticated USING (
        EXISTS (SELECT 1 FROM public.projects WHERE projects.id = readings.project_id AND projects.user_id = auth.uid())
    );

-- 9. Audit Log: Read if owner of project
DROP POLICY IF EXISTS "Users can read own audit log" ON public.audit_log;
CREATE POLICY "Users can read own audit log" ON public.audit_log
    FOR SELECT TO authenticated USING (
        auth.uid() = user_id OR
        EXISTS (SELECT 1 FROM public.projects WHERE projects.id = audit_log.project_id AND projects.user_id = auth.uid())
    );

-- 10. Library Tables: Public read for all authenticated users
DROP POLICY IF EXISTS "Public read for library boards" ON public.library_boards;
CREATE POLICY "Public read for library boards" ON public.library_boards
    FOR SELECT TO authenticated, anon USING (true);

DROP POLICY IF EXISTS "Public read for library peripherals" ON public.library_peripherals;
CREATE POLICY "Public read for library peripherals" ON public.library_peripherals
    FOR SELECT TO authenticated, anon USING (true);

DROP POLICY IF EXISTS "Public read for driver blocks" ON public.driver_blocks;
CREATE POLICY "Public read for driver blocks" ON public.driver_blocks
    FOR SELECT TO authenticated, anon USING (true);

DROP POLICY IF EXISTS "Public read for patterns" ON public.patterns;
CREATE POLICY "Public read for patterns" ON public.patterns
    FOR SELECT TO authenticated, anon USING (true);
