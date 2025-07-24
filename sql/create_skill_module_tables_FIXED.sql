-- Create skill_module table for Memory Maker Crew Production Ready feature
-- This table stores skill module definitions that can be used as memory contexts

-- Create skill_modules table
CREATE TABLE IF NOT EXISTS skill_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50),
    active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT skill_modules_name_version_unique UNIQUE (name, version)
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_skill_modules_name ON skill_modules(name);
CREATE INDEX IF NOT EXISTS idx_skill_modules_active ON skill_modules(active);
CREATE INDEX IF NOT EXISTS idx_skill_modules_created_at ON skill_modules(created_at);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_skill_modules_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER skill_modules_updated_at_trigger
    BEFORE UPDATE ON skill_modules
    FOR EACH ROW
    EXECUTE FUNCTION update_skill_modules_updated_at();

-- Add comment to document the table
COMMENT ON TABLE skill_modules IS 'Stores skill module definitions that provide specialized knowledge and procedures for agents';
COMMENT ON COLUMN skill_modules.id IS 'Unique identifier for the skill module';
COMMENT ON COLUMN skill_modules.name IS 'Human-readable name of the skill module';
COMMENT ON COLUMN skill_modules.description IS 'Detailed description of what the skill module provides';
COMMENT ON COLUMN skill_modules.version IS 'Version identifier for the skill module';
COMMENT ON COLUMN skill_modules.active IS 'Whether this skill module is currently active and available';
COMMENT ON COLUMN skill_modules.metadata IS 'Additional metadata about the skill module (JSON)';

-- Insert CORRECT skill modules for testing
-- THESE ARE TOOLS, NOT CAPABILITIES!
INSERT INTO skill_modules (name, description, version, metadata) VALUES
    (
        'microsoft_365',
        'Complete Microsoft 365 suite knowledge including Word, Excel, PowerPoint, Teams, SharePoint, and Outlook',
        '1.0.0',
        '{
            "tools": ["word", "excel", "powerpoint", "teams", "sharepoint", "outlook", "onedrive"],
            "capabilities": {
                "word": ["document_formatting", "mail_merge", "templates", "collaboration"],
                "excel": ["formulas", "pivot_tables", "macros", "data_analysis", "charts"],
                "powerpoint": ["presentations", "animations", "templates", "collaboration"],
                "teams": ["meetings", "channels", "file_sharing", "video_calls"],
                "sharepoint": ["sites", "lists", "workflows", "permissions"],
                "outlook": ["email", "calendar", "contacts", "tasks"]
            },
            "integration_level": "full",
            "subscription_tier": "premium"
        }'::jsonb
    ),
    (
        'google_workspace',
        'Complete Google Workspace knowledge including Docs, Sheets, Slides, Meet, Drive, and Gmail',
        '1.0.0',
        '{
            "tools": ["docs", "sheets", "slides", "meet", "drive", "gmail", "calendar"],
            "capabilities": {
                "docs": ["document_creation", "collaboration", "comments", "suggestions"],
                "sheets": ["formulas", "pivot_tables", "apps_script", "charts", "filters"],
                "slides": ["presentations", "themes", "animations", "collaboration"],
                "meet": ["video_calls", "screen_sharing", "recording", "breakout_rooms"],
                "drive": ["file_storage", "sharing", "permissions", "team_drives"],
                "gmail": ["email", "filters", "labels", "delegation"]
            },
            "integration_level": "full",
            "subscription_tier": "premium"
        }'::jsonb
    ),
    (
        'odoo_erp',
        'Odoo ERP system knowledge covering all modules including Sales, Inventory, Accounting, HR, and Manufacturing',
        '16.0',
        '{
            "modules": ["sales", "crm", "inventory", "accounting", "hr", "manufacturing", "project"],
            "capabilities": {
                "sales": ["quotations", "sales_orders", "invoicing", "reporting"],
                "inventory": ["warehouse_management", "stock_moves", "lot_tracking", "valuation"],
                "accounting": ["journal_entries", "reconciliation", "reporting", "tax_management"],
                "hr": ["employees", "contracts", "timesheets", "leaves", "expenses"],
                "manufacturing": ["bom", "work_orders", "planning", "quality_control"]
            },
            "deployment": "cloud",
            "subscription_tier": "enterprise"
        }'::jsonb
    ),
    (
        'salesforce_crm',
        'Salesforce CRM platform knowledge including Sales Cloud, Service Cloud, and Marketing Cloud basics',
        '2024.0',
        '{
            "clouds": ["sales_cloud", "service_cloud", "marketing_cloud_basics"],
            "objects": ["leads", "accounts", "contacts", "opportunities", "cases", "campaigns"],
            "features": {
                "sales": ["lead_management", "opportunity_tracking", "forecasting", "quotes"],
                "service": ["case_management", "knowledge_base", "sla", "omni_channel"],
                "automation": ["workflow_rules", "process_builder", "flow", "approval_processes"],
                "reporting": ["reports", "dashboards", "einstein_analytics_basics"]
            },
            "api_access": true,
            "subscription_tier": "professional"
        }'::jsonb
    ),
    (
        'quickbooks_online',
        'QuickBooks Online accounting software for small to medium businesses',
        '2024.0',
        '{
            "modules": ["banking", "expenses", "invoicing", "payroll", "reporting", "tax"],
            "capabilities": {
                "banking": ["bank_feeds", "reconciliation", "transfers", "deposits"],
                "invoicing": ["create_invoices", "recurring_invoices", "payment_tracking", "estimates"],
                "expenses": ["bill_entry", "expense_tracking", "vendor_management", "purchase_orders"],
                "reporting": ["profit_loss", "balance_sheet", "cash_flow", "custom_reports"],
                "payroll": ["employee_setup", "pay_runs", "tax_filings", "direct_deposit"]
            },
            "integrations": ["bank_connections", "payment_processors", "time_tracking"],
            "subscription_tier": "plus"
        }'::jsonb
    )
ON CONFLICT (name, version) DO NOTHING;

-- Update object_schemas to support skill_module actor type
UPDATE object_schemas 
SET schema = jsonb_set(
    schema,
    '{properties,actor_type,enum}',
    '["synth", "human", "client", "synth_class", "skill_module"]'::jsonb
),
updated_at = NOW()
WHERE name = 'memory_maker_crew' AND object_type = 'crew';

-- Also update the base_observation schema to support skill_module
UPDATE object_schemas 
SET schema = jsonb_set(
    schema,
    '{properties,actor_type,enum}',
    '["synth", "human", "client", "synth_class", "skill_module"]'::jsonb
),
updated_at = NOW()
WHERE name = 'base_observation' AND object_type = 'observation';

-- Grant appropriate permissions (adjust based on your user setup)
-- GRANT SELECT, INSERT, UPDATE ON skill_modules TO your_app_user;
-- GRANT USAGE ON SEQUENCE skill_modules_id_seq TO your_app_user;