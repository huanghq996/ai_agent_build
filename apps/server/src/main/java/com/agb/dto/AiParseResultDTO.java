package com.agb.dto;

import lombok.Data;
import java.math.BigDecimal;

@Data
public class AiParseResultDTO {
    private String type;
    private BigDecimal amount;
    private String category;
    private String remark;
    private String scheduleTitle;
    private String scheduleTime;
    private Integer smokingCount;
}
