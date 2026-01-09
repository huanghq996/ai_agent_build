package com.agb.service;

import com.agb.entity.Bill;
import com.agb.mapper.BillMapper;
import com.mybatisflex.core.paginate.Page;
import com.mybatisflex.core.query.QueryWrapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import static com.agb.entity.table.BillTableDef.BILL;

@Service
@RequiredArgsConstructor
public class BillService {
    private final BillMapper billMapper;

    public Page<Bill> list(Long userId, Long ledgerId, int page, int size) {
        QueryWrapper qw = QueryWrapper.create()
            .where(BILL.USER_ID.eq(userId));
        if (ledgerId != null) {
            qw.and(BILL.LEDGER_ID.eq(ledgerId));
        }
        qw.orderBy(BILL.BILL_DATE.desc());
        return billMapper.paginate(page, size, qw);
    }

    public Bill create(Long userId, Bill bill) {
        bill.setUserId(userId);
        billMapper.insert(bill);
        return bill;
    }

    public void update(Bill bill) {
        billMapper.update(bill);
    }

    public void delete(Long id) {
        billMapper.deleteById(id);
    }
}
