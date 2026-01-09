package com.agb.service;

import com.agb.dto.*;
import com.agb.entity.User;
import com.agb.mapper.UserMapper;
import com.agb.security.JwtUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import static com.agb.entity.table.UserTableDef.USER;

@Service
@RequiredArgsConstructor
public class AuthService {
    private final UserMapper userMapper;
    private final JwtUtil jwtUtil;

    public void register(RegisterRequest req) {
        User user = new User();
        user.setUsername(req.getUsername());
        user.setPassword(req.getPassword());
        user.setNickname(req.getNickname());
        user.setStatus(1);
        userMapper.insert(user);
    }

    public LoginResponse login(LoginRequest req) {
        User user = userMapper.selectOneByCondition(
            USER.USERNAME.eq(req.getUsername())
        );
        if (user == null || !user.getPassword().equals(req.getPassword())) {
            throw new RuntimeException("用户名或密码错误");
        }
        LoginResponse resp = new LoginResponse();
        resp.setToken(jwtUtil.generateToken(user.getId(), user.getUsername()));
        resp.setUserId(user.getId());
        resp.setUsername(user.getUsername());
        return resp;
    }
}
