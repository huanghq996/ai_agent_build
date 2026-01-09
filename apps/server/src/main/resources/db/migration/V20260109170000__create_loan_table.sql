CREATE TABLE `loan` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `type` TINYINT NOT NULL COMMENT '1:借出 2:借入',
    `person_name` VARCHAR(50) NOT NULL,
    `amount` DECIMAL(10,2) NOT NULL,
    `paid_amount` DECIMAL(10,2) DEFAULT 0,
    `status` TINYINT DEFAULT 0 COMMENT '0:未结清 1:已结清',
    `remark` VARCHAR(200),
    `loan_date` DATE NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_status` (`status`)
);
