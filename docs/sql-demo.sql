-- Run in a fresh practice database. No application database is required.
CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    amount INTEGER NOT NULL,
    status TEXT NOT NULL
);
INSERT INTO users VALUES (1, 'Anna'), (2, 'Boris'), (3, 'Vera');
INSERT INTO orders VALUES
    (101, 1, 700, 'paid'),
    (102, 1, 500, 'paid'),
    (103, 2, 900, 'paid'),
    (104, 2, 500, 'cancelled');

-- 5 rows: Anna twice, Boris twice, Vera once with NULL order_id.
SELECT u.name, o.id AS order_id
FROM users AS u
LEFT JOIN orders AS o ON o.user_id = u.id
ORDER BY u.id, o.id;

-- One row: user_id=1, total=1200.
SELECT user_id, SUM(amount) AS total
FROM orders
WHERE status = 'paid'
GROUP BY user_id
HAVING SUM(amount) > 1000;
