package com.agb.service;

import com.agb.dto.BillStatDTO;
import com.agb.dto.ScheduleStatDTO;
import com.agb.dto.SmokingStatDTO;
import com.agb.mapper.BillMapper;
import com.agb.mapper.ScheduleMapper;
import com.agb.mapper.SmokingMapper;
import com.mybatisflex.core.query.QueryMethods;
import com.mybatisflex.core.query.QueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

import static com.agb.entity.table.BillTableDef.BILL;
import static com.agb.entity.table.ScheduleTableDef.SCHEDULE;
import static com.agb.entity.table.SmokingTableDef.SMOKING;

@Service
@RequiredArgsConstructor
public class StatisticsService {
    private final BillMapper billMapper;
    private final SmokingMapper smokingMapper;
    private final ScheduleMapper scheduleMapper;

    public List<BillStatDTO> getBillStats(Long userId, String type, int days) {
        LocalDate endDate = LocalDate.now();
        LocalDate startDate = endDate.minusDays(days - 1);
        List<BillStatDTO> result = new ArrayList<>();

        for (LocalDate date = startDate; !date.isAfter(endDate); date = date.plusDays(1)) {
            BillStatDTO dto = new BillStatDTO();
            dto.setPeriod(date.toString());
            dto.setIncome(sumBillByDate(userId, date, 1));
            dto.setExpense(sumBillByDate(userId, date, 2));
            result.add(dto);
        }
        return result;
    }

    private BigDecimal sumBillByDate(Long userId, LocalDate date, int type) {
        QueryWrapper qw = QueryWrapper.create()
            .select(QueryMethods.sum(BILL.AMOUNT))
            .where(BILL.USER_ID.eq(userId))
            .and(BILL.BILL_DATE.eq(date))
            .and(BILL.TYPE.eq(type));
        Object sum = billMapper.selectObjectByQuery(qw);
        return sum != null ? (BigDecimal) sum : BigDecimal.ZERO;
    }

    public List<SmokingStatDTO> getSmokingStats(Long userId, int days) {
        LocalDate endDate = LocalDate.now();
        LocalDate startDate = endDate.minusDays(days - 1);
        List<SmokingStatDTO> result = new ArrayList<>();

        for (LocalDate date = startDate; !date.isAfter(endDate); date = date.plusDays(1)) {
            SmokingStatDTO dto = new SmokingStatDTO();
            dto.setPeriod(date.toString());
            dto.setCount(countSmokingByDate(userId, date));
            result.add(dto);
        }
        return result;
    }

    private Integer countSmokingByDate(Long userId, LocalDate date) {
        LocalDateTime start = date.atStartOfDay();
        LocalDateTime end = date.plusDays(1).atStartOfDay();
        QueryWrapper qw = QueryWrapper.create()
            .select(QueryMethods.sum(SMOKING.COUNT))
            .where(SMOKING.USER_ID.eq(userId))
            .and(SMOKING.SMOKE_TIME.ge(start))
            .and(SMOKING.SMOKE_TIME.lt(end));
        Object sum = smokingMapper.selectObjectByQuery(qw);
        return sum != null ? ((Number) sum).intValue() : 0;
    }

    public ScheduleStatDTO getScheduleStats(Long userId) {
        ScheduleStatDTO dto = new ScheduleStatDTO();
        dto.setTotal(countScheduleByStatus(userId, null));
        dto.setCompleted(countScheduleByStatus(userId, 1));
        dto.setPending(countScheduleByStatus(userId, 0));
        return dto;
    }

    private Integer countScheduleByStatus(Long userId, Integer status) {
        QueryWrapper qw = QueryWrapper.create()
            .where(SCHEDULE.USER_ID.eq(userId));
        if (status != null) {
            qw.and(SCHEDULE.STATUS.eq(status));
        }
        return (int) scheduleMapper.selectCountByQuery(qw);
    }
}
