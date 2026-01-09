package com.agb.controller;

import com.agb.entity.Loan;
import com.agb.service.LoanService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import java.math.BigDecimal;
import java.util.List;

@RestController
@RequestMapping("/api/loans")
@RequiredArgsConstructor
public class LoanController {
    private final LoanService loanService;

    @GetMapping
    public List<Loan> list(HttpServletRequest req,
                          @RequestParam(required = false) Integer status) {
        Long userId = (Long) req.getAttribute("userId");
        return loanService.listByUser(userId, status);
    }

    @PostMapping
    public Loan create(HttpServletRequest req, @RequestBody Loan loan) {
        Long userId = (Long) req.getAttribute("userId");
        return loanService.create(userId, loan);
    }

    @PostMapping("/{id}/repay")
    public void repay(@PathVariable Long id, @RequestParam BigDecimal amount) {
        loanService.repay(id, amount);
    }
}
