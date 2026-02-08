-- Adicionar tabela de manutenção de caçambas
USE fox_db;

CREATE TABLE IF NOT EXISTS dumpster_maintenance (
    id VARCHAR(36) PRIMARY KEY,
    dumpster_id VARCHAR(36) NOT NULL,
    reason TEXT,
    supplier VARCHAR(255),
    start_date DATETIME NOT NULL,
    expected_end_date DATETIME,
    actual_end_date DATETIME,
    estimated_cost DECIMAL(10, 2),
    actual_cost DECIMAL(10, 2),
    notes TEXT,
    status ENUM('in_progress', 'completed', 'cancelled') NOT NULL DEFAULT 'in_progress',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_dumpster_id (dumpster_id),
    INDEX idx_status (status),
    INDEX idx_start_date (start_date),
    FOREIGN KEY (dumpster_id) REFERENCES dumpsters(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
