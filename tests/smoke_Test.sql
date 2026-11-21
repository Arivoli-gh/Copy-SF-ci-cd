-- tests/smoke_tests.sql
USE ROLE CICD_DEPLOY_ROLE;
USE WAREHOUSE CICD_WH;
USE DATABASE IDENTIFIER('{{ db_name }}');
 
-- Fail if the expected objects are missing (division by zero raises an error)
SELECT 1 / IFF(COUNT(*) >= 3, 1, 0) AS objects_ok
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'APP';
 
-- Fail if the view cannot be queried
SELECT COUNT(*) FROM APP.CUSTOMER_ORDERS;
