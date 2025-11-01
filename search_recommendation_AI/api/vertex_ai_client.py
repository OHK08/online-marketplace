# ============================================================================
# FILE: api/vertex_ai_client.py
# ============================================================================
import logging
from google.cloud import aiplatform_v1beta1 as aiplatform
from vertexai.preview.vision_models import MultiModalEmbeddingModel
from vertexai import init as vertexai_init
from google.api_core.client_options import ClientOptions
from config import config

logger = logging.getLogger(__name__)


class VertexAIClient:
    """Vertex AI client for embeddings and vector similarity search."""

    def __init__(self):
        """Initialize Vertex AI client and MatchServiceClient."""
        try:
            # Initialize Vertex AI SDK context
            vertexai_init(
                project=config.gcp_project_id,
                location=config.vertex_ai_location
            )

            # Set up the MatchServiceClient (used for nearest neighbor search)
            if not config.vertex_ai_public_domain:
                raise ValueError("VERTEX_AI_PUBLIC_DOMAIN is not configured!")

            self.matching_client = aiplatform.MatchServiceClient(
                client_options=ClientOptions(
                    api_endpoint=config.vertex_ai_public_domain
                )
            )

            # Store necessary IDs
            self.deployed_index_id = config.vertex_ai_deployed_index_id
            self.index_endpoint_name = config.vertex_ai_endpoint_id

            logger.info("✅ Vertex AI MatchServiceClient initialized successfully")
            logger.info(f"  → Project ID: {config.gcp_project_id}")
            logger.info(f"  → Region: {config.vertex_ai_location}")
            logger.info(f"  → Public Domain: {config.vertex_ai_public_domain}")
            logger.info(f"  → Deployed Index ID: {self.deployed_index_id}")

        except Exception as e:
            logger.error(f"❌ Error initializing Vertex AI client: {e}", exc_info=True)
            raise RuntimeError("Failed to initialize Vertex AI client") from e

    # ------------------------------------------------------------------------
    # ✅ Generate Text Embedding (used for semantic search)
    # ------------------------------------------------------------------------
    def get_text_embedding(self, text: str):
        """Generate an embedding vector for text using Vertex AI's multimodal model."""
        try:
            model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")
            response = model.get_embeddings(contextual_text=text)
            vector = response.text_embedding
            logger.info(f"✅ Generated text embedding for '{text[:50]}...' ({len(vector)} dims)")
            return vector
        except Exception as e:
            logger.error(f"❌ Error generating text embedding: {e}", exc_info=True)
            raise RuntimeError("Failed to generate text embedding") from e

    # ------------------------------------------------------------------------
    # ✅ Find neighbors by vector
    # ------------------------------------------------------------------------
    def find_neighbors_by_vector(self, vector, num_neighbors=10, restricts=None):
        """Find nearest neighbors in the deployed Vertex AI Matching Engine index."""
        try:
            from google.cloud.aiplatform_v1beta1.types import (
                FindNeighborsRequest,
                IndexDatapoint,
            )

            request = FindNeighborsRequest(
                index_endpoint=self.index_endpoint_name,
                deployed_index_id=self.deployed_index_id,
                queries=[
                        FindNeighborsRequest.Query(
                            neighbor_count=num_neighbors,
                            datapoint=IndexDatapoint(feature_vector=vector)
                        )
                ],
            )

            response = self.matching_client.find_neighbors(request=request)
            ids = [
                neighbor.datapoint.datapoint_id
                for neighbor in response.nearest_neighbors[0].neighbors
            ]
            logger.info(f"✅ Found {len(ids)} neighbors via Vertex AI vector search")
            return ids

        except Exception as e:
            logger.error(f"Vertex AI neighbor search failed: {e}", exc_info=True)
            return []





    # ------------------------------------------------------------------------
    # ✅ Find neighbors by datapoint ID
    # ------------------------------------------------------------------------
    def find_neighbors_by_id(self, artwork_id: str, num_neighbors: int = 5):
        """Find nearest neighbors in Vertex AI Vector Search using datapoint ID."""
        try:
            logger.info(f"🔍 Finding neighbors for artwork ID: {artwork_id}")

            request = aiplatform.FindNeighborsRequest(
                index_endpoint=self.index_endpoint_name,
                deployed_index_id=self.deployed_index_id,
                queries=[
                    aiplatform.FindNeighborsRequest.Query(
                        datapoint=aiplatform.IndexDatapoint(
                            datapoint_id=artwork_id
                        ),
                        neighbor_count=num_neighbors
                    )
                ],
            )

            response = self.matching_client.find_neighbors(request=request)

            neighbor_ids = [
                neighbor.datapoint.datapoint_id
                for neighbor in response.nearest_neighbors[0].neighbors
            ]

            logger.info(f"✅ Found {len(neighbor_ids)} neighbors: {neighbor_ids}")
            return neighbor_ids

        except Exception as e:
            logger.error(f"❌ Error finding neighbors by ID: {e}", exc_info=True)
            raise


# Shared instance for reuse
vertex_ai_client = VertexAIClient()
