package com.agb.config;

import com.agb.security.AdminInterceptor;
import com.agb.security.JwtInterceptor;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.*;

@Configuration
@RequiredArgsConstructor
public class WebConfig implements WebMvcConfigurer {
    private final JwtInterceptor jwtInterceptor;
    private final AdminInterceptor adminInterceptor;

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(jwtInterceptor)
            .addPathPatterns("/api/**")
            .excludePathPatterns("/api/auth/**", "/api/admin/login", "/health");
        registry.addInterceptor(adminInterceptor)
            .addPathPatterns("/api/admin/**")
            .excludePathPatterns("/api/admin/login");
    }
}
