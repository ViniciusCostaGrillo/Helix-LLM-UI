import os
import unittest
import logging

from backend.knowledge.knowledge_builder import KnowledgeBuilderAgent
from backend.knowledge.watchdog import KnowledgeWatchdog
from backend.knowledge.knowledge_registry import KnowledgeRegistry
from backend.database.chroma_client import ChromaClientManager
from backend.themes.theme_agent import ThemeAgent
from backend.skills.skill_engine import SkillEngine

# Configure logger to print logs to stdout for validation
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestKnowledgeEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        self.watchdog = KnowledgeWatchdog()
        self.registry = KnowledgeRegistry()
        self.builder = KnowledgeBuilderAgent()
        self.chroma = ChromaClientManager()

        # Files to clean up later
        self.created_files = []

    def tearDown(self) -> None:
        logger.info("Cleaning up test artifacts...")
        for f in self.created_files:
            if os.path.exists(f):
                os.remove(f)
                logger.info(f"Removed temporary test file: {f}")
        # Clean up database registry entries if needed
        try:
            import sqlite3

            with sqlite3.connect(self.registry.db_path) as conn:
                for f in self.created_files:
                    norm_path = os.path.relpath(f, self.base_dir).replace("\\", "/")
                    conn.execute(
                        "DELETE FROM registry WHERE file_path = ?", (norm_path,)
                    )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to clean up SQLite registry: {e}")

    def test_theme_agent_resolutions(self) -> None:
        logger.info("--- Testing ThemeAgent resolution capabilities ---")
        agent = ThemeAgent()

        luxury_theme = agent.resolve_theme("luxury")
        self.assertEqual(luxury_theme["name"], "Luxury Gold Theme")
        self.assertEqual(luxury_theme["accent_color"], "#d4af37")

        glass_theme = agent.resolve_theme("glass")
        self.assertEqual(glass_theme["name"], "Glassmorphism Theme")
        self.assertIn("backdrop_filter", glass_theme["extra_styles"])

        fallback_theme = agent.resolve_theme("unknown_theme_style")
        self.assertEqual(fallback_theme["name"], "Dark Theme")

    def test_skill_engine_rules(self) -> None:
        logger.info("--- Testing SkillEngine design rules matching ---")
        engine = SkillEngine()
        luxury_rules = engine.resolve_skill_rules("luxury")
        self.assertTrue(any("gold" in rule.lower() for rule in luxury_rules))

    def test_knowledge_ingestion_loop(self) -> None:
        logger.info("--- Testing Knowledge Watchdog & Builder Extraction Loop ---")

        # 1. Create a mock component file in monitored folder
        mock_component_content = """import React from 'react';
export const TestCard = () => {
  return (
    <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl">
      <h3 className="text-white text-lg font-bold">Premium Card</h3>
      <p className="text-slate-400 mt-2">Ingestion test component</p>
    </div>
  );
};
"""
        comp_in_path = os.path.join(
            self.base_dir, "knowledge_input", "components", "TestCard.tsx"
        )
        with open(comp_in_path, "w", encoding="utf-8") as f:
            f.write(mock_component_content)
        self.created_files.append(comp_in_path)

        # 2. Create a mock design system file in monitored folder
        mock_design_content = """name: Luxury Gold Design System
rules:
  - Use high-contrast gold text colors
  - Apply thin borders
  - Incorporate generous whitespace margins
"""
        ds_in_path = os.path.join(
            self.base_dir, "knowledge_input", "design_systems", "luxury_design.yaml"
        )
        with open(ds_in_path, "w", encoding="utf-8") as f:
            f.write(mock_design_content)
        self.created_files.append(ds_in_path)

        # 3. Scan directories using the watchdog
        logger.info("Triggering manual watchdog directory scan...")
        self.watchdog.scan_once()

        # 4. Assert files are compiled to library folders
        comp_out_path = os.path.join(
            self.base_dir, "component_library", "cards", "TestCard.tsx"
        )
        ds_out_path = os.path.join(
            self.base_dir, "design_systems", "luxury", "luxury_design.yaml"
        )

        self.created_files.append(comp_out_path)
        self.created_files.append(ds_out_path)

        self.assertTrue(
            os.path.exists(comp_out_path), "Component was not compiled to library path!"
        )
        self.assertTrue(
            os.path.exists(ds_out_path),
            "Design system was not compiled to design_systems path!",
        )

        # Verify registry entry is logged as success
        norm_comp_path = os.path.relpath(comp_in_path, self.base_dir).replace("\\", "/")
        norm_ds_path = os.path.relpath(ds_in_path, self.base_dir).replace("\\", "/")

        self.assertTrue(
            self.registry.is_file_processed(
                norm_comp_path, self.builder.generate_hash(comp_in_path)
            )
        )
        self.assertTrue(
            self.registry.is_file_processed(
                norm_ds_path, self.builder.generate_hash(ds_in_path)
            )
        )

        # 5. Query ChromaDB to verify sync and collection metadata
        logger.info("Querying ChromaDB vector indexes to verify correct indexing...")

        # Test component retrieval in ChromaDB
        comp_query = self.chroma.query_similarity(
            collection_name="Components", query_vector=[0.1] * 128, limit=1
        )
        self.assertTrue(
            len(comp_query.results) > 0, "No results indexed in Components collection!"
        )
        self.assertEqual(
            comp_query.results[0].metadata.get("file_name"), "TestCard.tsx"
        )

        # Test design system retrieval in ChromaDB
        ds_query = self.chroma.query_similarity(
            collection_name="DesignSystems", query_vector=[0.1] * 128, limit=1
        )
        self.assertTrue(
            len(ds_query.results) > 0, "No results indexed in DesignSystems collection!"
        )
        self.assertEqual(
            ds_query.results[0].metadata.get("file_name"), "luxury_design.yaml"
        )
        self.assertEqual(ds_query.results[0].metadata.get("design_rules_count"), 3)

        logger.info(
            "All assertions passed. Knowledge Watchdog Ingestion loop verified successfully!"
        )


if __name__ == "__main__":
    unittest.main()
