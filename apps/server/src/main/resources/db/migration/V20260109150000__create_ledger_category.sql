CREATE TABLE `ledger` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `name` VARCHAR(50) NOT NULL,
    `description` VARCHAR(200),
    `is_default` TINYINT DEFAULT 0,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_user_id` (`user_id`)
);

CREATE TABLE `category` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `user_id` BIGINT,
    `parent_id` BIGINT DEFAULT 0,
    `name` VARCHAR(50) NOT NULL,
    `type` TINYINT NOT NULL COMMENT '1:支出 2:收入',
    `is_system` TINYINT DEFAULT 0,
    `sort_order` INT DEFAULT 0,
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_parent_id` (`parent_id`)
);
