"""
Agentic AutoML Intelligence Platform — Software Integration Templates (Section 53)
Provides production code snippets in TypeScript, Java, and cURL for external systems.
"""

TYPESCRIPT_EXAMPLE = """
// TypeScript / Node.js Production Integration Example
import axios from 'axios';

interface PredictionRequest {
  entity_id?: string;
  features: Record<string, any>;
}

interface PredictionResponse {
  request_id: string;
  prediction: number | string;
  model_version: string;
  latency_ms: number;
}

const client = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 5000,
});

async function scoreTransaction(customerId: string, amount: number) {
  const response = await client.post<PredictionResponse>('/predict', {
    entity_id: customerId,
    features: {
      transaction_amount: amount,
      currency: 'USD',
      device_risk_score: 0.12,
    },
  });

  console.log(`Predicted fraud status: ${response.data.prediction} (v: ${response.data.model_version}) in ${response.data.latency_ms}ms`);
  return response.data;
}
"""

JAVA_EXAMPLE = """
// Java (Java 11+ HttpClient) Production Integration Example
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

public class AutoMLClient {
    private static final HttpClient client = HttpClient.newBuilder()
        .connectTimeout(Duration.ofSeconds(5))
        .build();

    public static String predict(String entityId, String jsonFeatures) throws Exception {
        String requestBody = String.format("{\\"entity_id\\": \\"%s\\", \\"features\\": %s}", entityId, jsonFeatures);

        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create("http://localhost:8000/api/v1/predict"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(requestBody))
            .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        return response.body();
    }
}
"""

CURL_EXAMPLE = """
# Real-Time Prediction Request via cURL
curl -X POST http://localhost:8000/api/v1/predict \\
  -H "Content-Type: application/json" \\
  -d '{
    "entity_id": "cust_98234",
    "features": {
      "transaction_amount": 420.50,
      "merchant_category": "electronics",
      "velocity_24h": 3
    }
  }'

# Stream Change Data Capture Event via cURL
curl -X POST http://localhost:8000/api/v1/cdc/events \\
  -H "Content-Type: application/json" \\
  -d '{
    "source": "postgres.public.orders",
    "entity_id": "order_78912",
    "operation": "INSERT",
    "payload": {
      "customer_id": "cust_98234",
      "total_amount": 420.50,
      "status": "completed"
    }
  }'

# Check Real-Time Model Health and Drift Status
curl -X GET http://localhost:8000/api/v1/models/primary/health
"""
