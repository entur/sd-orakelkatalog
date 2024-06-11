package no.digdir.fdk.orakelbackend;

import com.pgvector.PGvector;
import dev.langchain4j.data.embedding.Embedding;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

@Service
public class PostgresService {

    private static final int NUM_MATCHES = 7;
    private static final double SIM_THRESHOLD = 0.3;

    private final JdbcTemplate jdbcTemplate;

    public PostgresService(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<Map<String, Object>> matchDatasetsByVector(Embedding embedding) {
        PGvector vector = new PGvector(embedding.vector());
        List<Map<String, Object>> results = jdbcTemplate.queryForList("""
                    WITH vector_matches AS (
                            SELECT id,
                                    1 - (embedding <=> ?) AS similarity
                            FROM dataset_embeddings
                            WHERE 1 - (embedding <=> ?) > ?
                            ORDER BY similarity DESC
                            LIMIT ?
                    )
                    SELECT *
                    FROM datasets
                    WHERE id IN (SELECT id FROM vector_matches)
        """, vector, vector, SIM_THRESHOLD, NUM_MATCHES);
        return results;
    }
}
