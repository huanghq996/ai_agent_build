package com.agb.controller;

import com.agb.entity.Ledger;
import com.agb.service.LedgerService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/ledgers")
@RequiredArgsConstructor
public class LedgerController {
    private final LedgerService ledgerService;

    @GetMapping
    public List<Ledger> list(HttpServletRequest req) {
        Long userId = (Long) req.getAttribute("userId");
        return ledgerService.listByUser(userId);
    }

    @PostMapping
    public Ledger create(HttpServletRequest req, @RequestBody Ledger ledger) {
        Long userId = (Long) req.getAttribute("userId");
        return ledgerService.create(userId, ledger.getName(), ledger.getDescription());
    }

    @DeleteMapping("/{id}")
    public void delete(@PathVariable Long id) {
        ledgerService.delete(id);
    }
}
