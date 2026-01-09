package com.agb.entity;

import com.mybatisflex.annotation.Id;
import com.mybatisflex.annotation.KeyType;
import com.mybatisflex.annotation.Table;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@Table("ledger")
public class Ledger {
    @Id(keyType = KeyType.Auto)
    private Long id;
    private Long userId;
    private String name;
    private String description;
    private Integer isDefault;
    private LocalDateTime createdAt;
}
