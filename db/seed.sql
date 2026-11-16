-- ========================================================
-- EduPulse Demo Seed Script
-- Compatible with SQLite
-- ========================================================

-- 1. CLEANUP EXISTING DATA (Optional, ensures fresh state)
DELETE FROM assignments;
DELETE FROM cie_records;
DELETE FROM users;

-- 2. INSERT DEMO USERS
-- Default Password for all accounts: password123
-- SHA-256 hash of 'password123':
-- ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f

INSERT INTO users (usn, name, password_hash) VALUES 
('4NI23CS001', 'Govardhan G S', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f'),
('4NI23CS002', 'Gaddam Lakshmi Chaitanya Reddy', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f'),
('4NI23CS003', 'Kopparapu Damini', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f'),
('4NI23CS004', 'Kishan M Y', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f'),
('4NI23CS005', 'G Sreenidhi', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f');

-- 3. INSERT SAMPLE CIE RECORDS (For Govardhan - 4NI23CS001)
-- Demonstrating both Passing/Eligible subjects and Warning/Cutoff scenarios
INSERT INTO cie_records (usn, subject, test1, test2, lab_cie, total_cie) VALUES
-- CDD: ((22 + 24) / 2) + (46 / 2) = 23 + 23 = 46.0 / 50 (Strong Eligible)
('4NI23CS001', 'Collaborative Dev & DevOps (1BCS303)', 22.0, 24.0, 46.0, 46.0),

-- Operating Systems: ((18 + 19) / 2) + (38 / 2) = 18.5 + 19 = 37.5 / 50 (Eligible)
('4NI23CS001', 'Operating Systems', 18.0, 19.0, 38.0, 37.5),

-- DBMS: ((10 + 12) / 2) + (16 / 2) = 11 + 8 = 19.0 / 50 (Ineligible Demo: < 20 cutoff)
('4NI23CS001', 'Database Management Systems', 10.0, 12.0, 16.0, 19.0);

-- 4. INSERT ASSIGNMENTS TO TRIGGER ALL 5 STATUS BADGES DYNAMICALLY
-- Uses SQLite's DATE('now') so the status badges always work on any test day!
INSERT INTO assignments (usn, subject, title, due_date, is_completed) VALUES
-- 🟢 Green – Completed
('4NI23CS001', 'Collaborative Dev & DevOps (1BCS303)', 'Exp 1: Git Installation & Local Repo Configuration', DATE('now', '-10 days'), 1),
('4NI23CS001', 'Collaborative Dev & DevOps (1BCS303)', 'Exp 2: Remote Sync with Push, Pull, Fetch', DATE('now', '-7 days'), 1),

-- 🔴 Red – Overdue (Past deadline and not completed)
('4NI23CS001', 'Database Management Systems', 'Mini Assignment: ER Diagram & Normalization', DATE('now', '-3 days'), 0),

-- 🟠 Orange – Due Today (Deadline matches current system date)
('4NI23CS001', 'Collaborative Dev & DevOps (1BCS303)', 'Exp 6: Automated CI Workflow with GitHub Actions', DATE('now'), 0),

-- 🟡 Yellow – Due Soon (1 to 2 days remaining)
('4NI23CS001', 'Operating Systems', 'Lab Exercise: CPU Scheduling Simulation in C', DATE('now', '+1 day'), 0),
('4NI23CS001', 'Collaborative Dev & DevOps (1BCS303)', 'Exp 10: Multi-Container Setup via Docker Compose', DATE('now', '+2 days'), 0),

-- 🔵 Blue – Upcoming (More than 2 days remaining)
('4NI23CS001', 'Collaborative Dev & DevOps (1BCS303)', 'Exp 14: Final Mini Project Deployment & Viva', DATE('now', '+7 days'), 0),
('4NI23CS001', 'Discrete Mathematical Structures', 'Assignment 3: Graph Theory & Recurrence Relations', DATE('now', '+12 days'), 0);