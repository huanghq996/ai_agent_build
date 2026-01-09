package com.agb.service;

import com.agb.entity.Ledger;
import com.agb.mapper.LedgerMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.List;

import static com.agb.entity.table.LedgerTableDef.LEDGER;

@Service
@RequiredArgsConstructor
public class LedgerService {
    private final LedgerMapper ledgerMapper;

    public List<Ledger> listByUser(Long userId) {
        return ledgerMapper.selectListByCondition(LEDGER.USER_ID.eq(userId));
    }

    public Ledger create(Long userId, String name, String desc) {
        Ledger ledger = new Ledger();
        ledger.setUserId(userId);
        ledger.setName(name);
        ledger.setDescription(desc);
        ledgerMapper.insert(ledger);
        return ledger;
    }

    public void delete(Long id) {
        ledgerMapper.deleteById(id);
    }
}
