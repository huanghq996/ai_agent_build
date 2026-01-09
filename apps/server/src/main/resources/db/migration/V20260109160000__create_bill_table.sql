CREATE TABLE `bill` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `ledger_id` BIGINT NOT NULL,
    `category_id` BIGINT NOT NULL,
    `type` TINYINT NOT NULL COMMENT '1:支出 2:收入',
    `amount` DECIMAL(10,2) NOT NULL,
    `remark` VARCHAR(200),
    `tags` VARCHAR(200),
    `bill_date` DATE NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_ledger_id` (`ledger_id`),
    INDEX `idx_bill_date` (`bill_date`)
);
