package com.agb.config;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.context.annotation.Configuration;

@Configuration
@MapperScan("com.agb.mapper")
public class MyBatisFlexConfig {
}
