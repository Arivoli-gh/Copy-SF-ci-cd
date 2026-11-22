-- deploy_all.sql : executed INSIDE Snowflake from the Git repository
-- Variables are passed with: EXECUTE IMMEDIATE FROM ... USING (db_name => '...', commit_sha => '...')
USE ROLE CICD_DEPLOY_ROLE;
USE WAREHOUSE CICD_WH;
USE DATABASE IDENTIFIER('{{ db_name }}');
 
-- Ordered, idempotent migrations (paths are relative to this file)
EXECUTE IMMEDIATE FROM './Migration/V1.0.0__deployment20261121.sql';
EXECUTE IMMEDIATE FROM './Migration/V1.0.0__deployment20261122.sql';
 
-- Audit trail
INSERT INTO CICD_DB.OPS.DEPLOY_LOG
  SELECT '{{ db_name }}', '{{ commit_sha }}', CURRENT_TIMESTAMP();
