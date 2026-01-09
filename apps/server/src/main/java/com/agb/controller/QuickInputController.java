package com.agb.controller;

import com.agb.entity.QuickInput;
import com.agb.service.QuickInputService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/quick-input")
@RequiredArgsConstructor
public class QuickInputController {
    private final QuickInputService quickInputService;

    @GetMapping
    public List<QuickInput> list(HttpServletRequest req) {
        Long userId = (Long) req.getAttribute("userId");
        return quickInputService.list(userId);
    }

    @PostMapping
    public QuickInput create(HttpServletRequest req, @RequestBody QuickInput input) {
        Long userId = (Long) req.getAttribute("userId");
        return quickInputService.create(userId, input);
    }

    @PutMapping("/{id}")
    public QuickInput update(HttpServletRequest req, @PathVariable Long id, @RequestBody QuickInput input) {
        Long userId = (Long) req.getAttribute("userId");
        return quickInputService.update(userId, id, input);
    }

    @DeleteMapping("/{id}")
    public void delete(HttpServletRequest req, @PathVariable Long id) {
        Long userId = (Long) req.getAttribute("userId");
        quickInputService.delete(userId, id);
    }
}
