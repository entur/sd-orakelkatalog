package no.digdir.fdk.orakelbackend;

import dev.langchain4j.data.embedding.Embedding;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.*;

import org.slf4j.Logger;

@RestController
@RequestMapping("/api")
public class LLMController {

    private static final Logger logger = LoggerFactory.getLogger(LLMController.class);

    @Autowired
    private PostgresService postgresService;

    @Autowired
    private VertexService vertexService;

    @GetMapping("/fdkllm")
    public Map<String, Object> getLLMResponse(@RequestParam String query) {
        logger.info(query);
        Map<String, Object> response = new HashMap<>();
        Embedding embedding = vertexService.embed(query);
        logger.info(embedding.toString());
        List<Map<String, Object>> results = postgresService.matchDatasetsByVector(embedding);

        List<String> titles = results.stream()
                .map(result -> result.get("title").toString().toUpperCase())
                .toList();

        List<String> links = results.stream()
                .map(result -> result.get("link").toString())
                .toList();

        List<String> summaries = results.stream()
                .map(result -> result.get("summary").toString())
                .toList();

        String LLMResponse = vertexService.llmRequest(summaries, query);

        response.put("titles", titles);
        response.put("links", links);
        response.put("llm", LLMResponse);

        return response;
    }
}
