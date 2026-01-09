package com.agb.entity;

import com.mybatisflex.annotation.Id;
import com.mybatisflex.annotation.KeyType;
import com.mybatisflex.annotation.Table;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@Table("loan")
public class Loan {
    @Id(keyType = KeyType.Auto)
    private Long id;
    private Long userId;
    private Integer type;
    private String personName;
    private BigDecimal amount;
    private BigDecimal paidAmount;
    private Integer status;
    private String remark;
    private LocalDate loanDate;
    private LocalDateTime createdAt;
}
