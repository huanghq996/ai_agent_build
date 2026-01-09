package com.agb.entity;

import com.mybatisflex.annotation.Id;
import com.mybatisflex.annotation.KeyType;
import com.mybatisflex.annotation.Table;
import lombok.Data;

@Data
@Table("category")
public class Category {
    @Id(keyType = KeyType.Auto)
    private Long id;
    private Long userId;
    private Long parentId;
    private String name;
    private Integer type;
    private Integer isSystem;
    private Integer sortOrder;
}
