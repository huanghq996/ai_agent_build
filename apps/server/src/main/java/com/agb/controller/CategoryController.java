package com.agb.controller;

import com.agb.entity.Category;
import com.agb.service.CategoryService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/categories")
@RequiredArgsConstructor
public class CategoryController {
    private final CategoryService categoryService;

    @GetMapping
    public List<Category> list(HttpServletRequest req) {
        Long userId = (Long) req.getAttribute("userId");
        return categoryService.listByUser(userId);
    }

    @PostMapping
    public Category create(HttpServletRequest req, @RequestBody Category cat) {
        Long userId = (Long) req.getAttribute("userId");
        return categoryService.create(userId, cat);
    }

    @DeleteMapping("/{id}")
    public void delete(@PathVariable Long id) {
        categoryService.delete(id);
    }
}
