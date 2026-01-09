package com.agb.controller;

import com.agb.dto.BillStatDTO;
import com.agb.dto.ScheduleStatDTO;
import com.agb.dto.SmokingStatDTO;
import com.agb.service.StatisticsService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/statistics")
@RequiredArgsConstructor
public class StatisticsController {
    private final StatisticsService statisticsService;

    @GetMapping("/bill")
    public List<BillStatDTO> getBillStats(
            HttpServletRequest req,
            @RequestParam(defaultValue = "day") String type,
            @RequestParam(defaultValue = "7") int days) {
        Long userId = (Long) req.getAttribute("userId");
        return statisticsService.getBillStats(userId, type, days);
    }

    @GetMapping("/smoking")
    public List<SmokingStatDTO> getSmokingStats(
            HttpServletRequest req,
            @RequestParam(defaultValue = "7") int days) {
        Long userId = (Long) req.getAttribute("userId");
        return statisticsService.getSmokingStats(userId, days);
    }

    @GetMapping("/schedule")
    public ScheduleStatDTO getScheduleStats(HttpServletRequest req) {
        Long userId = (Long) req.getAttribute("userId");
        return statisticsService.getScheduleStats(userId);
    }
}
