"""
Job Management Service for Data Quality Platform

Handles:
- Job folder structure creation and management
- CSV file detection and processing coordination
- Use case agent execution
- Result storage and archival
"""

import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.config import settings
from app.db.models import JobRecord
from app.services.agents.uc1 import run_uc1_analysis, UC1AnalysisResult
from app.services.agents.uc4 import run_uc4_analysis, UC4AnalysisResult

logger = logging.getLogger(__name__)


class JobFolderStructure(BaseModel):
    """Represents the folder structure for a job"""
    
    job_id: int
    inputs_folder: Path
    outputs_folder: Path
    temp_folder: Path
    csv_files: List[Path] = Field(default_factory=list)


class JobProcessor:
    """Main job processing coordinator"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def setup_job_folders(self, job_id: int) -> JobFolderStructure:
        """
        Create the required folder structure for a job:
        - inputs/job_{id}/
        - outputs/job_{id}/
        - temp/job_{id}/
        """
        job_folder_name = f"job_{job_id}"
        
        # Create folder paths
        inputs_folder = settings.inputs_dir / job_folder_name
        outputs_folder = settings.outputs_dir / job_folder_name
        temp_folder = settings.temp_dir / job_folder_name
        
        # Create directories
        inputs_folder.mkdir(parents=True, exist_ok=True)
        outputs_folder.mkdir(parents=True, exist_ok=True)
        temp_folder.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created folder structure for job {job_id}")
        
        return JobFolderStructure(
            job_id=job_id,
            inputs_folder=inputs_folder,
            outputs_folder=outputs_folder,
            temp_folder=temp_folder
        )
    
    def detect_csv_files(self, inputs_folder: Path) -> List[Path]:
        """
        Scan the inputs folder for CSV files to process
        """
        csv_files = []
        
        if not inputs_folder.exists():
            logger.warning(f"Inputs folder does not exist: {inputs_folder}")
            return csv_files
        
        # Find all CSV files recursively
        for csv_file in inputs_folder.rglob("*.csv"):
            if csv_file.is_file():
                csv_files.append(csv_file)
                logger.info(f"Found CSV file: {csv_file}")
        
        logger.info(f"Found {len(csv_files)} CSV files in {inputs_folder}")
        return csv_files
    
    def get_reference_file(self, use_case: str) -> Optional[Path]:
        """
        Get the appropriate reference file from uploads folder based on use case
        """
        uploads_folder = settings.uploads_dir
        
        # Look for reference files with naming convention: uc1_reference.csv, uc4_reference.csv, etc.
        reference_patterns = [
            f"{use_case}_reference.csv",
            f"{use_case.upper()}_reference.csv",
            f"reference_{use_case}.csv",
            f"reference_{use_case.upper()}.csv"
        ]
        
        for pattern in reference_patterns:
            ref_file = uploads_folder / pattern
            if ref_file.exists():
                logger.info(f"Found reference file for {use_case}: {ref_file}")
                return ref_file
        
        # If no specific reference found, look for any CSV in uploads
        csv_files = list(uploads_folder.glob("*.csv"))
        if csv_files:
            ref_file = csv_files[0]  # Use the first available CSV
            logger.info(f"Using generic reference file for {use_case}: {ref_file}")
            return ref_file
        
        logger.warning(f"No reference file found for use case {use_case}")
        return None
    
    def create_use_case_temp_folder(self, job_temp_folder: Path, use_case: str) -> Path:
        """
        Create temp sub-folder for specific use case: temp/job_{id}/uc_{use_case}
        """
        uc_temp_folder = job_temp_folder / f"uc_{use_case}"
        uc_temp_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created use case temp folder: {uc_temp_folder}")
        return uc_temp_folder
    
    async def process_csv_with_uc1(
        self, 
        csv_file: Path, 
        reference_file: Optional[Path],
        temp_folder: Path,
        job_id: int
    ) -> UC1AnalysisResult:
        """
        Process a single CSV file with UC1 (sparse data detection)
        """
        logger.info(f"Processing {csv_file} with UC1 agent")
        
        # Create unique filename for this processing
        unique_filename = f"uc1_{job_id}_{csv_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Run UC1 analysis
        result = await run_uc1_analysis(
            file_path=str(csv_file),
            reference_file_path=str(reference_file) if reference_file else None,
            unique_filename=unique_filename
        )
        
        # Copy input file to temp folder for archival
        temp_input_file = temp_folder / f"input_{csv_file.name}"
        shutil.copy2(csv_file, temp_input_file)
        logger.info(f"Archived input file to: {temp_input_file}")
        
        return result
    
    async def process_csv_with_uc4(
        self, 
        csv_file: Path, 
        temp_folder: Path,
        job_id: int
    ) -> UC4AnalysisResult:
        """
        Process a single CSV file with UC4 (duplicate detection and removal)
        """
        logger.info(f"Processing {csv_file} with UC4 agent")
        
        # Create unique filename for this processing
        unique_filename = f"uc4_{job_id}_{csv_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Run UC4 analysis
        result = await run_uc4_analysis(
            file_path=str(csv_file),
            unique_filename=unique_filename
        )
        
        # Save cleaned CSV to temp folder
        if hasattr(result, 'output_file_path') and result.output_file_path:
            temp_output_file = temp_folder / f"cleaned_{csv_file.name}"
            if Path(result.output_file_path).exists():
                shutil.copy2(result.output_file_path, temp_output_file)
                logger.info(f"Saved cleaned CSV to: {temp_output_file}")
        
        return result
    
    async def execute_job_workflow(self, job_id: int, selected_use_cases: List[str]) -> Dict:
        """
        Execute the complete job workflow:
        1. Setup job folders
        2. Detect CSV files in inputs
        3. Process each CSV with selected use cases
        4. Store results and manage temp/output folders
        """
        logger.info(f"Starting job workflow for job {job_id} with use cases: {selected_use_cases}")
        
        # Setup folder structure
        job_structure = self.setup_job_folders(job_id)
        
        # Update job record with folder paths
        job_record = self.db.query(JobRecord).filter(JobRecord.id == job_id).first()
        if job_record:
            job_record.inputs_folder = str(job_structure.inputs_folder)
            job_record.outputs_folder = str(job_structure.outputs_folder)
            job_record.temp_folder = str(job_structure.temp_folder)
            self.db.commit()
        
        # Detect CSV files
        csv_files = self.detect_csv_files(job_structure.inputs_folder)
        job_structure.csv_files = csv_files
        
        if not csv_files:
            logger.warning(f"No CSV files found in {job_structure.inputs_folder}")
            return {"status": "no_files", "message": "No CSV files found to process"}
        
        # Process each use case
        results = {}
        
        for use_case in selected_use_cases:
            logger.info(f"Processing use case: {use_case}")
            
            # Update job record with current use case
            if job_record:
                job_record.use_case = use_case
                job_record.status = f"processing_{use_case}"
                self.db.commit()
            
            # Create use case temp folder
            uc_temp_folder = self.create_use_case_temp_folder(job_structure.temp_folder, use_case)
            
            # Get reference file if needed
            reference_file = None
            if use_case.lower() == "uc1":
                reference_file = self.get_reference_file(use_case.lower())
            
            # Process each CSV file
            uc_results = []
            for csv_file in csv_files:
                try:
                    if use_case.lower() == "uc1":
                        result = await self.process_csv_with_uc1(
                            csv_file, reference_file, uc_temp_folder, job_id
                        )
                    elif use_case.lower() == "uc4":
                        result = await self.process_csv_with_uc4(
                            csv_file, uc_temp_folder, job_id
                        )
                    else:
                        logger.error(f"Unknown use case: {use_case}")
                        continue
                    
                    uc_results.append(result)
                    logger.info(f"Successfully processed {csv_file} with {use_case}")
                    
                except Exception as e:
                    logger.error(f"Error processing {csv_file} with {use_case}: {str(e)}")
                    continue
            
            results[use_case] = uc_results
        
        # Save final output to job's output folder
        await self.save_final_output(job_structure, results, selected_use_cases)
        
        # Update job status
        if job_record:
            job_record.status = "completed"
            job_record.completed_at = datetime.utcnow()
            job_record.use_case = None  # Clear current use case
            self.db.commit()
        
        logger.info(f"Job {job_id} workflow completed successfully")
        return {"status": "completed", "results": results}
    
    async def save_final_output(
        self, 
        job_structure: JobFolderStructure, 
        results: Dict, 
        selected_use_cases: List[str]
    ):
        """
        Save final output of the last use case to the job's output folder
        """
        if not results or not selected_use_cases:
            return
        
        # Get results from the last use case
        last_use_case = selected_use_cases[-1]
        last_results = results.get(last_use_case, [])
        
        if not last_results:
            logger.warning(f"No results found for final use case: {last_use_case}")
            return
        
        # Copy final results to outputs folder
        for i, result in enumerate(last_results):
            if hasattr(result, 'output_file_path') and result.output_file_path:
                output_file = Path(result.output_file_path)
                if output_file.exists():
                    final_output = job_structure.outputs_folder / f"final_result_{i+1}_{output_file.name}"
                    shutil.copy2(output_file, final_output)
                    logger.info(f"Saved final output: {final_output}")
        
        # Create summary report
        summary_file = job_structure.outputs_folder / "job_summary.txt"
        with open(summary_file, 'w') as f:
            f.write(f"Job {job_structure.job_id} Processing Summary\n")
            f.write(f"Completed at: {datetime.now()}\n")
            f.write(f"Use cases executed: {', '.join(selected_use_cases)}\n")
            f.write(f"CSV files processed: {len(job_structure.csv_files)}\n")
            f.write("\nResults:\n")
            for use_case, uc_results in results.items():
                f.write(f"  {use_case}: {len(uc_results)} files processed\n")
        
        logger.info(f"Created job summary: {summary_file}")
