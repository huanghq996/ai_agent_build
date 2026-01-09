package com.agb.service;

import com.agb.dto.AiParseResultDTO;
import com.agb.entity.AiConfig;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class AiParseService {
    private final AiConfigService aiConfigService;
    private final ObjectMapper objectMapper = new ObjectMapper();
    private final RestTemplate restTemplate = new RestTemplate();

    private static final String SYSTEM_PROMPT = """
        你是一个智能助手，负责解析用户输入并提取结构化数据。
        根据用户输入，识别以下类型之一：
        1. bill - 记账（包含金额、分类、备注）
        2. smoking - 抽烟记录
        3. schedule - 日程安排（包含标题、时间）

        返回JSON格式：
        {"type":"bill|smoking|schedule","amount":数字,"category":"分类","remark":"备注","scheduleTitle":"标题","scheduleTime":"时间","smokingCount":数量}
        只返回JSON，不要其他内容。
        """;

    public AiParseResultDTO parse(Long userId, String input) throws Exception {
        AiConfig config = aiConfigService.getByUserId(userId);
        if (config == null) {
            throw new RuntimeException("请先配置AI设置");
        }

        String response = callAi(config, input);
        return objectMapper.readValue(response, AiParseResultDTO.class);
    }

    private String callAi(AiConfig config, String input) throws Exception {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("Authorization", "Bearer " + config.getApiKey());

        Map<String, Object> body = Map.of(
            "model", config.getModel(),
            "messages", List.of(
                Map.of("role", "system", "content", SYSTEM_PROMPT),
                Map.of("role", "user", "content", input)
            )
        );

        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);
        ResponseEntity<String> resp = restTemplate.exchange(
            config.getEndpoint(), HttpMethod.POST, entity, String.class);

        JsonNode root = objectMapper.readTree(resp.getBody());
        return root.path("choices").get(0).path("message").path("content").asText();
    }
}
