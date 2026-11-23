INSERT INTO APP.CUSTOMERS (CUSTOMER_ID, FULL_NAME, EMAIL) VALUES
  (101, 'Aarav Sharma', 'aarav.sharma@example.com'),
  (102, 'Priya Nair', 'priya.nair@example.com'),
  (103, 'Rohan Verma', 'rohan.verma@example.com'),
  (104, 'Ananya Iyer', 'ananya.iyer@example.com'),
  (105, 'Vikram Patel', NULL);
INSERT INTO APP.ORDERS (ORDER_ID, CUSTOMER_ID, AMOUNT, ORDER_TS) VALUES
  (5001, 101, 1499.50, '2026-11-18 10:15:00'),
  (5002, 102, 450.00,  '2026-11-19 14:30:25'),
  (5003, 101, 2999.99, '2026-11-20 09:05:10'),
  (5004, 103, 125.75,  '2026-11-21 18:45:00'),
  (5005, 104, 890.20,  DEFAULT);
