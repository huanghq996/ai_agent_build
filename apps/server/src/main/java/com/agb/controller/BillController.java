package com.agb.controller;

import com.agb.entity.Bill;
import com.agb.service.BillService;
import com.mybatisflex.core.paginate.Page;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/bills")
@RequiredArgsConstructor
public class BillController {
    private final BillService billService;

    @GetMapping
    public Page<Bill> list(HttpServletRequest req,
                          @RequestParam(required = false) Long ledgerId,
                          @RequestParam(defaultValue = "1") int page,
                          @RequestParam(defaultValue = "20") int size) {
        Long userId = (Long) req.getAttribute("userId");
        return billService.list(userId, ledgerId, page, size);
    }

    @PostMapping
    public Bill create(HttpServletRequest req, @RequestBody Bill bill) {
        Long userId = (Long) req.getAttribute("userId");
        return billService.create(userId, bill);
    }

    @PutMapping("/{id}")
    public void update(@PathVariable Long id, @RequestBody Bill bill) {
        bill.setId(id);
        billService.update(bill);
    }

    @DeleteMapping("/{id}")
    public void delete(@PathVariable Long id) {
        billService.delete(id);
    }
}
