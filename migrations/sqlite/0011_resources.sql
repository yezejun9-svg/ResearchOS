CREATE UNIQUE INDEX budget_provider_event ON domain_objects(project, json_extract(body,'$.provider_event_id')) WHERE kind='BudgetLedgerEntry';
CREATE UNIQUE INDEX resource_open_key ON domain_objects(project, json_extract(body,'$.dedup_key')) WHERE kind='ResourceRequest' AND json_extract(body,'$.status') IN ('OPEN','ACKNOWLEDGED');
