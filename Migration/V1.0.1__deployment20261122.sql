-- CUSTOMERS (CUSTOMER_ID and CREATED_AT are auto-populated)
TRUNCATE TABLE APP.CUSTOMERS;
TRUNCATE TABLE APP.ORDERS;
INSERT INTO APP.CUSTOMERS (FULL_NAME, EMAIL) VALUES
  ('Aarav Sharma',   'aarav.sharma@example.com'),
  ('Priya Nair',     'priya.nair@example.com'),
  ('Rahul Verma',    'rahul.verma@example.com'),
  ('Ananya Iyer',    'ananya.iyer@example.com'),
  ('Karthik Reddy',  NULL);

-- ORDERS (ORDER_ID and ORDER_TS are auto-populated)
INSERT INTO APP.ORDERS (CUSTOMER_ID, AMOUNT) VALUES
  (1, 1499.00),
  (2,  249.50),
  (3, 8999.99),
  (4,  620.75),
  (1,  310.00);
