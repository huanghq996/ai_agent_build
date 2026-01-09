package com.agb.controller;

import com.agb.dto.AiParseResultDTO;
import com.agb.entity.AiConfig;
import com.agb.service.AiConfigService;
import com.agb.service.AiParseService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/ai")
@RequiredArgsConstructor
public class AiController {
    private final AiConfigService aiConfigService;
    private final AiParseService aiParseService;

    @GetMapping("/config")
    public AiConfig getConfig(HttpServletRequest req) {
        Long userId = (Long) req.getAttribute("userId");
        return aiConfigService.getByUserId(userId);
    }

    @PostMapping("/config")
    public AiConfig saveConfig(HttpServletRequest req, @RequestBody AiConfig config) {
        Long userId = (Long) req.getAttribute("userId");
        return aiConfigService.saveOrUpdate(userId, config);
    }

    @PostMapping("/parse")
    public AiParseResultDTO parse(HttpServletRequest req, @RequestBody Map<String, String> body) throws Exception {
        Long userId = (Long) req.getAttribute("userId");
        String input = body.get("input");
        return aiParseService.parse(userId, input);
    }
}
