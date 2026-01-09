package com.agb.service;

import com.agb.entity.QuickInput;
import com.agb.mapper.QuickInputMapper;
import com.mybatisflex.core.query.QueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.List;

import static com.agb.entity.table.QuickInputTableDef.QUICK_INPUT;

@Service
@RequiredArgsConstructor
public class QuickInputService {
    private final QuickInputMapper quickInputMapper;

    public List<QuickInput> list(Long userId) {
        QueryWrapper qw = QueryWrapper.create()
            .where(QUICK_INPUT.USER_ID.eq(userId))
            .orderBy(QUICK_INPUT.SORT_ORDER.asc());
        return quickInputMapper.selectListByQuery(qw);
    }

    public QuickInput create(Long userId, QuickInput input) {
        input.setUserId(userId);
        quickInputMapper.insert(input);
        return input;
    }

    public QuickInput update(Long userId, Long id, QuickInput input) {
        QueryWrapper qw = QueryWrapper.create()
            .where(QUICK_INPUT.ID.eq(id))
            .and(QUICK_INPUT.USER_ID.eq(userId));
        input.setId(null);
        input.setUserId(null);
        quickInputMapper.updateByQuery(input, qw);
        return quickInputMapper.selectOneById(id);
    }

    public void delete(Long userId, Long id) {
        QueryWrapper qw = QueryWrapper.create()
            .where(QUICK_INPUT.ID.eq(id))
            .and(QUICK_INPUT.USER_ID.eq(userId));
        quickInputMapper.deleteByQuery(qw);
    }
}
