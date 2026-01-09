package com.agb.dto;

import lombok.Data;
import java.math.BigDecimal;

@Data
public class BillStatDTO {
    private String period;
    private BigDecimal income;
    private BigDecimal expense;
}
