package com.agb.entity;

import com.mybatisflex.annotation.Id;
import com.mybatisflex.annotation.KeyType;
import com.mybatisflex.annotation.Table;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@Table("schedule")
public class Schedule {
    @Id(keyType = KeyType.Auto)
    private Long id;
    private Long userId;
    private String title;
    private String content;
    private LocalDateTime remindTime;
    private Integer status;
    private LocalDateTime createdAt;
}
