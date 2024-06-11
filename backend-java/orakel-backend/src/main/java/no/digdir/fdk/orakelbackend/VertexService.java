package no.digdir.fdk.orakelbackend;

import dev.langchain4j.data.embedding.Embedding;
import dev.langchain4j.model.input.Prompt;
import dev.langchain4j.model.input.PromptTemplate;
import dev.langchain4j.model.vertexai.VertexAiEmbeddingModel;
import dev.langchain4j.model.vertexai.VertexAiLanguageModel;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class VertexService {

    private static final String VERTEX_MODEL_NAME = "text-bison@002";
    private static final String EMBEDDING_MODEL_NAME = "textembedding-gecko-multilingual";

    private static final String PROMPT_TEMPLATE = """
            You will be given a detailed description of different datasets in norwegian
            enclosed in triple backticks (```) and a question or query enclosed in
            double backticks(``).
            Select all datasets that are relevant to answer the question.
            Proritize datasets with newer data.
            Using those dataset descriptions, answer the following
            question in as much detail as possible.
            Give your answer in Norwegian.
            You should only use the information in the descriptions.
            Your answer should include the dataset title and why each dataset match the question posed by the user.
            If no datasets are given, explain that the data may not exist.
            Give the answer in Markdown and mark the dataset title as bold text.
                    
            Description:
            ```{{descriptions}}```
                    
                    
            Question:
            ``{{user_query}}``
                    
                    
            Answer:
            """;

    private final VertexAiLanguageModel vertex;
    private final PromptTemplate promptTemplate;
    private final VertexAiEmbeddingModel embeddingModel;

    public  VertexService() {
        this.vertex = VertexAiLanguageModel.builder()
                .endpoint("us-central1-aiplatform.googleapis.com:443")
                .project("")
                .location("")
                .publisher("google")
                .modelName(VERTEX_MODEL_NAME)
                .maxOutputTokens(1000)
                .topK(1)
                .build();

        this.promptTemplate = PromptTemplate.from(PROMPT_TEMPLATE);

        this.embeddingModel = VertexAiEmbeddingModel.builder()
                .endpoint("europe-north1-aiplatform.googleapis.com:443")
                .project("")
                .location("")
                .publisher("google")
                .modelName(EMBEDDING_MODEL_NAME)
                .build();
    }

    public Embedding embed(String query) {
        return embeddingModel.embed(query).content();
    }

    public String llmRequest(List<String> summaries, String query) {
        Map<String, Object> variables = new HashMap<>();
        variables.put("descriptions", summaries);
        variables.put("user_query", query);

        Prompt prompt = promptTemplate.apply(variables);
        String response = vertex.generate(prompt).content();
        return response;
    }

}
