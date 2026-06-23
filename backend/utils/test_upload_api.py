import os
import unittest
from fastapi.testclient import TestClient

from backend.api.main import app


class TestUploadAPI(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        self.created_files = []

    def tearDown(self) -> None:
        # Clean up files created during upload testing
        for f in self.created_files:
            if os.path.exists(f):
                os.remove(f)

    def test_file_classification_and_upload(self) -> None:
        # 1. Prepare multiple test files with diverse extensions
        files_data = [
            (
                "HeaderComponent.tsx",
                b"export const Header = () => <header />;",
                "components",
            ),
            ("saas_design_rules.yaml", b"theme: saas\nrules: []", "design_systems"),
            ("motion_skill_spec.yml", b"animation: gsap", "skills"),
            ("system_prompt_template.json", b"{}", "prompt_templates"),
            ("logo_icon.svg", b"<svg />", "images"),
            ("ambient_video.mp4", b"mp4_binary_content", "videos"),
            ("3d_globe.glb", b"glb_binary_content", "3d"),
            (
                "references_links.txt",
                b"https://example.com/layout1\nhttps://example.com/layout2",
                "references",
            ),
        ]

        files_payload = []
        for filename, content, expected_category in files_data:
            files_payload.append(
                ("files", (filename, content, "application/octet-stream"))
            )

        # 2. Trigger Upload API Endpoint
        response = self.client.post("/knowledge/upload", files=files_payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()

        self.assertIn("uploaded_files", data)
        self.assertEqual(data["count"], len(files_data))

        # 3. Assert correct folder classifications and filesystem outcomes
        for res in data["uploaded_files"]:
            filename = res["filename"]
            category = res["category"]
            target_path = res["target_path"]
            status = res["status"]

            # Find matching expectation
            expected = next((item for item in files_data if item[0] == filename), None)
            self.assertIsNotNone(expected)
            self.assertEqual(category, expected[2])
            self.assertEqual(status, "success")

            # Check that file exists on disk
            full_path = os.path.join(self.base_dir, target_path)
            self.assertTrue(
                os.path.exists(full_path), f"File {filename} was not saved on disk!"
            )
            self.created_files.append(full_path)

        # 4. Verify listing endpoint displays uploaded files
        list_response = self.client.get("/knowledge/files")
        self.assertEqual(list_response.status_code, 200)
        list_data = list_response.json()

        for filename, _, category in files_data:
            category_list = list_data.get(category, [])
            file_names = [f["name"] for f in category_list]
            self.assertIn(
                filename,
                file_names,
                f"Uploaded file {filename} not listed in category {category}",
            )


if __name__ == "__main__":
    unittest.main()
