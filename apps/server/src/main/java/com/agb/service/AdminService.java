package com.agb.service;

import com.agb.dto.*;
import com.agb.entity.Admin;
import com.agb.mapper.AdminMapper;
import com.agb.security.JwtUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import static com.agb.entity.table.AdminTableDef.ADMIN;

@Service
@RequiredArgsConstructor
public class AdminService {
    private final AdminMapper adminMapper;
    private final JwtUtil jwtUtil;

    public LoginResponse login(LoginRequest req) {
        Admin admin = adminMapper.selectOneByCondition(
            ADMIN.USERNAME.eq(req.getUsername())
        );
        if (admin == null || !admin.getPassword().equals(req.getPassword())) {
            throw new RuntimeException("用户名或密码错误");
        }
        LoginResponse resp = new LoginResponse();
        resp.setToken(jwtUtil.generateToken(admin.getId(), "admin:" + admin.getUsername()));
        resp.setUserId(admin.getId());
        resp.setUsername(admin.getUsername());
        return resp;
    }
}
