-- Criar banco de dados
CREATE DATABASE IF NOT EXISTS fox_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE fox_db;

-- Tabela de usuários
CREATE TABLE IF NOT EXISTS users (
    email VARCHAR(255) PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de clientes
CREATE TABLE IF NOT EXISTS clients (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50) NOT NULL,
    address TEXT NOT NULL,
    document VARCHAR(50) NOT NULL,
    document_type ENUM('cpf', 'cnpj') NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_document (document),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de caçambas
CREATE TABLE IF NOT EXISTS dumpsters (
    id VARCHAR(36) PRIMARY KEY,
    identifier VARCHAR(100) NOT NULL UNIQUE,
    size VARCHAR(50) NOT NULL,
    capacity VARCHAR(50) NOT NULL,
    description TEXT,
    status ENUM('available', 'rented', 'maintenance', 'in_transit') NOT NULL DEFAULT 'available',
    current_location TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_identifier (identifier)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de pedidos
CREATE TABLE IF NOT EXISTS orders (
    id VARCHAR(36) PRIMARY KEY,
    client_id VARCHAR(36) NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    dumpster_id VARCHAR(36) NOT NULL,
    dumpster_identifier VARCHAR(100) NOT NULL,
    order_type ENUM('placement', 'removal', 'exchange') NOT NULL,
    status ENUM('pending', 'in_progress', 'completed', 'cancelled') NOT NULL DEFAULT 'pending',
    delivery_address TEXT NOT NULL,
    rental_value DECIMAL(10, 2) NOT NULL,
    payment_method ENUM('cash', 'credit_card', 'debit_card', 'bank_transfer', 'pix') NOT NULL,
    scheduled_date DATETIME NOT NULL,
    completed_date DATETIME,
    notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_client_id (client_id),
    INDEX idx_dumpster_id (dumpster_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (dumpster_id) REFERENCES dumpsters(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de contas a pagar
CREATE TABLE IF NOT EXISTS accounts_payable (
    id VARCHAR(36) PRIMARY KEY,
    description VARCHAR(255) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    due_date DATETIME NOT NULL,
    paid_date DATETIME,
    category VARCHAR(100) NOT NULL,
    is_paid BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_due_date (due_date),
    INDEX idx_is_paid (is_paid),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de contas a receber
CREATE TABLE IF NOT EXISTS accounts_receivable (
    id VARCHAR(36) PRIMARY KEY,
    client_id VARCHAR(36) NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    order_id VARCHAR(36) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    due_date DATETIME NOT NULL,
    received_date DATETIME,
    is_received BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_client_id (client_id),
    INDEX idx_order_id (order_id),
    INDEX idx_due_date (due_date),
    INDEX idx_is_received (is_received),
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
