package com.agb.security;

import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import org.springframework.stereotype.Component;
import javax.crypto.SecretKey;
import java.util.Date;

@Component
public class JwtUtil {
    private static final String SECRET = "agb-secret-key-for-jwt-token-2024-must-be-longer";
    private static final long EXPIRATION = 86400000L;
    private final SecretKey key = Keys.hmacShaKeyFor(SECRET.getBytes());

    public String generateToken(Long userId, String username) {
        return Jwts.builder()
            .subject(userId.toString())
            .claim("username", username)
            .issuedAt(new Date())
            .expiration(new Date(System.currentTimeMillis() + EXPIRATION))
            .signWith(key)
            .compact();
    }

    public Long getUserId(String token) {
        Claims claims = Jwts.parser()
            .verifyWith(key).build()
            .parseSignedClaims(token).getPayload();
        return Long.parseLong(claims.getSubject());
    }

    public boolean validate(String token) {
        try {
            Jwts.parser().verifyWith(key).build().parseSignedClaims(token);
            return true;
        } catch (JwtException e) {
            return false;
        }
    }
}
