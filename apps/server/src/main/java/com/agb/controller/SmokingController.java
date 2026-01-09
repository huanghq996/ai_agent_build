package com.agb.controller;

import com.agb.entity.Smoking;
import com.agb.service.SmokingService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/smoking")
@RequiredArgsConstructor
public class SmokingController {
    private final SmokingService smokingService;

    @GetMapping
    public List<Smoking> list(HttpServletRequest req) {
        Long userId = (Long) req.getAttribute("userId");
        return smokingService.list(userId);
    }

    @PostMapping
    public Smoking create(HttpServletRequest req) {
        Long userId = (Long) req.getAttribute("userId");
        return smokingService.create(userId);
    }
}
