CREATE TABLE `ai_config` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL UNIQUE,
    `endpoint` VARCHAR(500) NOT NULL,
    `api_key` VARCHAR(500) NOT NULL,
    `model` VARCHAR(100) DEFAULT 'gpt-3.5-turbo',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_user_id` (`user_id`)
);
