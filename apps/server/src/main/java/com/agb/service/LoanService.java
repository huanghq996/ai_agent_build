package com.agb.service;

import com.agb.entity.Loan;
import com.agb.mapper.LoanMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.math.BigDecimal;
import java.util.List;

import static com.agb.entity.table.LoanTableDef.LOAN;

@Service
@RequiredArgsConstructor
public class LoanService {
    private final LoanMapper loanMapper;

    public List<Loan> listByUser(Long userId, Integer status) {
        var qw = LOAN.USER_ID.eq(userId);
        if (status != null) {
            qw = qw.and(LOAN.STATUS.eq(status));
        }
        return loanMapper.selectListByCondition(qw);
    }

    public Loan create(Long userId, Loan loan) {
        loan.setUserId(userId);
        loan.setPaidAmount(BigDecimal.ZERO);
        loan.setStatus(0);
        loanMapper.insert(loan);
        return loan;
    }

    public void repay(Long id, BigDecimal amount) {
        Loan loan = loanMapper.selectOneById(id);
        BigDecimal newPaid = loan.getPaidAmount().add(amount);
        loan.setPaidAmount(newPaid);
        if (newPaid.compareTo(loan.getAmount()) >= 0) {
            loan.setStatus(1);
        }
        loanMapper.update(loan);
    }
}
