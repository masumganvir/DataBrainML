"""
DataWise AI — Agent 15: Reporting & Notebook Agent Implementation
"""

from pathlib import Path
import time
from typing import Any, Dict, Optional
import zipfile
from loguru import logger

from .schemas import AgentInput, AgentOutput
from tools.notebook import NotebookGenerator
from tools.reporting import generate_html_report, generate_pdf_report, generate_markdown_report


class NotebookAgent:
    """Agent 15: Generates 35-section Jupyter notebook, HTML/PDF/MD reports, and production ZIP bundle."""

    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self.agent_name = "Reporting & Notebook Agent"

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        try:
            if input_data.dataset_path and Path(input_data.dataset_path).exists():
                out_dir = Path("artifacts") / input_data.session_id
                out_dir.mkdir(parents=True, exist_ok=True)

                ts = int(time.time())
                dataset_name = Path(input_data.dataset_path).stem

                # 1. Generate 35-section Jupyter notebook
                nb_file = str(out_dir / f"project_{dataset_name}_{ts}.ipynb")
                state_dict = {
                    "dataset_path": input_data.dataset_path,
                    "target_column": input_data.parameters.get("target_column", "target"),
                    "ml_task_type": input_data.parameters.get("task_type", "classification"),
                    "selected_final_model": input_data.parameters.get("champion_model", "RandomForest"),
                }
                gen = NotebookGenerator(state_dict, project_name=f"DataWise_{dataset_name}")
                gen.generate(nb_file)

                # 2. Generate Reports
                html_file = str(out_dir / "analysis_report.html")
                pdf_file = str(out_dir / "analysis_report.pdf")
                md_file = str(out_dir / "analysis_report.md")

                generate_html_report(state_dict, output_path=html_file)
                generate_pdf_report(state_dict, output_path=pdf_file)
                generate_markdown_report(state_dict, output_path=md_file)

                # 3. Create ZIP bundle adhering to Section 29
                zip_path = out_dir / f"DataWise_{dataset_name}.zip"
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    # dataset/
                    zipf.write(input_data.dataset_path, arcname=f"dataset/{Path(input_data.dataset_path).name}")
                    # notebooks/
                    zipf.write(nb_file, arcname="notebooks/project_analysis.ipynb")
                    # reports/
                    zipf.write(html_file, arcname="reports/analysis_report.html")
                    zipf.write(md_file, arcname="reports/analysis_report.md")
                    if Path(pdf_file).exists():
                        zipf.write(pdf_file, arcname="reports/analysis_report.pdf")
                    # requirements & README
                    zipf.writestr("requirements.txt", "scikit-learn\npandas\nnumpy\nfastapi\nuvicorn\njoblib\n")
                    zipf.writestr("README.md", f"# DataWise AI Delivery Package: {dataset_name}\n\nProduced by DataWise AI.")
                    zipf.writestr("Dockerfile", "FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt\nCMD [\"python\", \"api/main.py\"]\n")

                summary = (
                    f"Reporting & Notebook Agent generated 35-section notebook, "
                    "HTML/PDF/MD reports, and complete project ZIP bundle."
                )
                return self.validate(AgentOutput(
                    session_id=input_data.session_id,
                    agent_name=self.agent_name,
                    status="success",
                    data={
                        "notebook_path": nb_file,
                        "html_report_path": html_file,
                        "pdf_report_path": pdf_file,
                        "markdown_report_path": md_file,
                        "project_bundle_path": str(zip_path.resolve()),
                    },
                    summary=summary,
                ))

            return self.validate(AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={"tool": "NotebookGenerator", "status": "ready"},
                summary="Reporting & Notebook Agent ready.",
            ))
        except Exception as e:
            logger.error(f"Error in Notebook Agent: {e}")
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                summary=f"Notebook Agent error: {str(e)}",
                warnings=[str(e)],
            )

    def validate(self, result: AgentOutput) -> AgentOutput:
        assert result.agent_name == self.agent_name
        return result
