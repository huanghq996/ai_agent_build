package com.agb.entity;

import com.mybatisflex.annotation.Id;
import com.mybatisflex.annotation.KeyType;
import com.mybatisflex.annotation.Table;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@Table("quick_input")
public class QuickInput {
    @Id(keyType = KeyType.Auto)
    private Long id;
    private Long userId;
    private String label;
    private String content;
    private Integer sortOrder;
    private LocalDateTime createdAt;
}
