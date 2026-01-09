package com.agb.controller;

import com.agb.entity.User;
import com.agb.service.UserService;
import com.mybatisflex.core.paginate.Page;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/admin/users")
@RequiredArgsConstructor
public class UserController {
    private final UserService userService;

    @GetMapping
    public Page<User> list(@RequestParam(defaultValue = "1") int page,
                           @RequestParam(defaultValue = "10") int size) {
        return userService.list(page, size);
    }

    @GetMapping("/{id}")
    public User getById(@PathVariable Long id) {
        return userService.getById(id);
    }

    @PutMapping("/{id}/status")
    public void updateStatus(@PathVariable Long id, @RequestParam Integer status) {
        userService.updateStatus(id, status);
    }
}
