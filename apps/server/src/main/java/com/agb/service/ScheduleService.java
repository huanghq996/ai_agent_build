package com.agb.service;

import com.agb.entity.Schedule;
import com.agb.mapper.ScheduleMapper;
import com.mybatisflex.core.query.QueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.List;

import static com.agb.entity.table.ScheduleTableDef.SCHEDULE;

@Service
@RequiredArgsConstructor
public class ScheduleService {
    private final ScheduleMapper scheduleMapper;

    public List<Schedule> list(Long userId, Integer status) {
        QueryWrapper qw = QueryWrapper.create()
            .where(SCHEDULE.USER_ID.eq(userId));
        if (status != null) {
            qw.and(SCHEDULE.STATUS.eq(status));
        }
        qw.orderBy(SCHEDULE.REMIND_TIME.asc());
        return scheduleMapper.selectListByQuery(qw);
    }

    public Schedule create(Long userId, Schedule s) {
        s.setUserId(userId);
        s.setStatus(0);
        scheduleMapper.insert(s);
        return s;
    }

    public void complete(Long userId, Long id) {
        QueryWrapper qw = QueryWrapper.create()
            .where(SCHEDULE.ID.eq(id))
            .and(SCHEDULE.USER_ID.eq(userId));
        Schedule s = new Schedule();
        s.setStatus(1);
        scheduleMapper.updateByQuery(s, qw);
    }

    public Schedule update(Long userId, Long id, Schedule s) {
        QueryWrapper qw = QueryWrapper.create()
            .where(SCHEDULE.ID.eq(id))
            .and(SCHEDULE.USER_ID.eq(userId));
        s.setId(null);
        s.setUserId(null);
        scheduleMapper.updateByQuery(s, qw);
        return scheduleMapper.selectOneById(id);
    }

    public void delete(Long userId, Long id) {
        QueryWrapper qw = QueryWrapper.create()
            .where(SCHEDULE.ID.eq(id))
            .and(SCHEDULE.USER_ID.eq(userId));
        scheduleMapper.deleteByQuery(qw);
    }

    public Schedule getById(Long userId, Long id) {
        QueryWrapper qw = QueryWrapper.create()
            .where(SCHEDULE.ID.eq(id))
            .and(SCHEDULE.USER_ID.eq(userId));
        return scheduleMapper.selectOneByQuery(qw);
    }
}
