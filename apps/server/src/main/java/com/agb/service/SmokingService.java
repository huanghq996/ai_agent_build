package com.agb.service;

import com.agb.entity.Smoking;
import com.agb.mapper.SmokingMapper;
import com.mybatisflex.core.query.QueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.time.LocalDateTime;
import java.util.List;

import static com.agb.entity.table.SmokingTableDef.SMOKING;

@Service
@RequiredArgsConstructor
public class SmokingService {
    private final SmokingMapper smokingMapper;

    public List<Smoking> list(Long userId) {
        QueryWrapper qw = QueryWrapper.create()
            .where(SMOKING.USER_ID.eq(userId))
            .orderBy(SMOKING.SMOKE_TIME.desc());
        return smokingMapper.selectListByQuery(qw);
    }

    public Smoking create(Long userId) {
        Smoking s = new Smoking();
        s.setUserId(userId);
        s.setCount(1);
        s.setSmokeTime(LocalDateTime.now());
        smokingMapper.insert(s);
        return s;
    }
}
