package com.agb.entity;

import com.mybatisflex.annotation.Id;
import com.mybatisflex.annotation.KeyType;
import com.mybatisflex.annotation.Table;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@Table("bill")
public class Bill {
    @Id(keyType = KeyType.Auto)
    private Long id;
    private Long userId;
    private Long ledgerId;
    private Long categoryId;
    private Integer type;
    private BigDecimal amount;
    private String remark;
    private String tags;
    private LocalDate billDate;
    private LocalDateTime createdAt;
}
