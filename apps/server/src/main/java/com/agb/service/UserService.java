package com.agb.service;

import com.agb.entity.User;
import com.agb.mapper.UserMapper;
import com.mybatisflex.core.paginate.Page;
import com.mybatisflex.core.query.QueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class UserService {
    private final UserMapper userMapper;

    public Page<User> list(int page, int size) {
        return userMapper.paginate(page, size, QueryWrapper.create());
    }

    public User getById(Long id) {
        return userMapper.selectOneById(id);
    }

    public void updateStatus(Long id, Integer status) {
        User user = new User();
        user.setId(id);
        user.setStatus(status);
        userMapper.update(user);
    }
}
