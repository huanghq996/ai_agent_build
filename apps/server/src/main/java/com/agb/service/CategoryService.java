package com.agb.service;

import com.agb.entity.Category;
import com.agb.mapper.CategoryMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.List;

import static com.agb.entity.table.CategoryTableDef.CATEGORY;

@Service
@RequiredArgsConstructor
public class CategoryService {
    private final CategoryMapper categoryMapper;

    public List<Category> listByUser(Long userId) {
        return categoryMapper.selectListByCondition(
            CATEGORY.USER_ID.eq(userId).or(CATEGORY.IS_SYSTEM.eq(1))
        );
    }

    public Category create(Long userId, Category cat) {
        cat.setUserId(userId);
        cat.setIsSystem(0);
        categoryMapper.insert(cat);
        return cat;
    }

    public void delete(Long id) {
        categoryMapper.deleteById(id);
    }
}
