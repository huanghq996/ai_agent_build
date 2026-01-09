package com.agb.entity;

import com.mybatisflex.annotation.Id;
import com.mybatisflex.annotation.KeyType;
import com.mybatisflex.annotation.Table;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@Table("ai_config")
public class AiConfig {
    @Id(keyType = KeyType.Auto)
    private Long id;
    private Long userId;
    private String endpoint;
    private String apiKey;
    private String model;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
