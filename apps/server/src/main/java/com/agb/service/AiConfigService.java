package com.agb.service;

import com.agb.entity.AiConfig;
import com.agb.mapper.AiConfigMapper;
import com.mybatisflex.core.query.QueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import static com.agb.entity.table.AiConfigTableDef.AI_CONFIG;

@Service
@RequiredArgsConstructor
public class AiConfigService {
    private final AiConfigMapper aiConfigMapper;

    public AiConfig getByUserId(Long userId) {
        QueryWrapper qw = QueryWrapper.create()
            .where(AI_CONFIG.USER_ID.eq(userId));
        return aiConfigMapper.selectOneByQuery(qw);
    }

    public AiConfig saveOrUpdate(Long userId, AiConfig config) {
        AiConfig existing = getByUserId(userId);
        if (existing != null) {
            config.setId(existing.getId());
            config.setUserId(userId);
            aiConfigMapper.update(config);
            return aiConfigMapper.selectOneById(existing.getId());
        } else {
            config.setUserId(userId);
            aiConfigMapper.insert(config);
            return config;
        }
    }
}
