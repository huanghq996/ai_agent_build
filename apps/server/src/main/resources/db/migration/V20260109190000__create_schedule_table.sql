CREATE TABLE `schedule` (
    `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `title` VARCHAR(100) NOT NULL,
    `content` VARCHAR(500),
    `remind_time` DATETIME,
    `status` TINYINT DEFAULT 0 COMMENT '0:待办 1:完成',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_remind_time` (`remind_time`)
);
