package com.agb.controller;

import com.agb.entity.Schedule;
import com.agb.service.ScheduleService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/schedule")
@RequiredArgsConstructor
public class ScheduleController {
    private final ScheduleService scheduleService;

    @GetMapping
    public List<Schedule> list(HttpServletRequest req,
                               @RequestParam(required = false) Integer status) {
        Long userId = (Long) req.getAttribute("userId");
        return scheduleService.list(userId, status);
    }

    @GetMapping("/{id}")
    public Schedule getById(HttpServletRequest req, @PathVariable Long id) {
        Long userId = (Long) req.getAttribute("userId");
        return scheduleService.getById(userId, id);
    }

    @PostMapping
    public Schedule create(HttpServletRequest req, @RequestBody Schedule schedule) {
        Long userId = (Long) req.getAttribute("userId");
        return scheduleService.create(userId, schedule);
    }

    @PutMapping("/{id}")
    public Schedule update(HttpServletRequest req,
                           @PathVariable Long id,
                           @RequestBody Schedule schedule) {
        Long userId = (Long) req.getAttribute("userId");
        return scheduleService.update(userId, id, schedule);
    }

    @PostMapping("/{id}/complete")
    public void complete(HttpServletRequest req, @PathVariable Long id) {
        Long userId = (Long) req.getAttribute("userId");
        scheduleService.complete(userId, id);
    }

    @DeleteMapping("/{id}")
    public void delete(HttpServletRequest req, @PathVariable Long id) {
        Long userId = (Long) req.getAttribute("userId");
        scheduleService.delete(userId, id);
    }
}
