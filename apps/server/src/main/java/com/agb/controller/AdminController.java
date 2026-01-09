package com.agb.controller;

import com.agb.dto.*;
import com.agb.service.AdminService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/admin")
@RequiredArgsConstructor
public class AdminController {
    private final AdminService adminService;

    @PostMapping("/login")
    public LoginResponse login(@RequestBody LoginRequest req) {
        return adminService.login(req);
    }
}
