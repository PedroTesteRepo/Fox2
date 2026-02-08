-- Migrations para múltiplos telefones e endereços de clientes
USE fox_db;

-- Tabela de telefones dos clientes
CREATE TABLE IF NOT EXISTS client_phones (
    id VARCHAR(36) PRIMARY KEY,
    client_id VARCHAR(36) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    phone_type VARCHAR(50) NOT NULL DEFAULT 'Celular',
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_client_id (client_id),
    INDEX idx_is_primary (is_primary),
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de endereços dos clientes
CREATE TABLE IF NOT EXISTS client_addresses (
    id VARCHAR(36) PRIMARY KEY,
    client_id VARCHAR(36) NOT NULL,
    address_type VARCHAR(50) NOT NULL DEFAULT 'Residencial',
    cep VARCHAR(9) NOT NULL,
    street VARCHAR(255) NOT NULL,
    number VARCHAR(20) NOT NULL,
    complement VARCHAR(255),
    neighborhood VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_client_id (client_id),
    INDEX idx_is_primary (is_primary),
    INDEX idx_cep (cep),
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Adicionar coluna na tabela orders para referenciar endereço do cliente
ALTER TABLE orders ADD COLUMN delivery_address_id VARCHAR(36) NULL AFTER delivery_address;
ALTER TABLE orders ADD INDEX idx_delivery_address_id (delivery_address_id);
-- Não adicionar FOREIGN KEY pois delivery_address_id é opcional (pode usar texto livre)

-- Script de migração: Copiar dados antigos de telefone e endereço para novas tabelas
-- Apenas para clientes que já existem no sistema

-- Migrar telefones existentes
INSERT INTO client_phones (id, client_id, phone, phone_type, is_primary, created_at)
SELECT 
    UUID() as id,
    id as client_id,
    phone,
    'Celular' as phone_type,
    TRUE as is_primary,
    created_at
FROM clients
WHERE phone IS NOT NULL AND phone != ''
AND NOT EXISTS (
    SELECT 1 FROM client_phones WHERE client_phones.client_id = clients.id
);

-- Migrar endereços existentes (tentar extrair informações do campo address)
INSERT INTO client_addresses (id, client_id, address_type, cep, street, number, complement, neighborhood, city, state, is_primary, created_at)
SELECT 
    UUID() as id,
    id as client_id,
    'Residencial' as address_type,
    '' as cep,
    address as street,
    'S/N' as number,
    '' as complement,
    '' as neighborhood,
    '' as city,
    '' as state,
    TRUE as is_primary,
    created_at
FROM clients
WHERE address IS NOT NULL AND address != ''
AND NOT EXISTS (
    SELECT 1 FROM client_addresses WHERE client_addresses.client_id = clients.id
);
