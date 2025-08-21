"""
Job Management Service for Data Quality Platform

Handles:
- Job folder structure creation and management
- CSV file detection and processing coordination
- Use case agent execution
- Result storage and archival
"""

import json
import shutil
import logging
import asyncio
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
    
    async def _broadcast_job_update(self, job_record):
        """Broadcast job status updates via WebSocket"""
        try:
            from app.websocket_manager import websocket_manager
            
            job_data = {
                "id": job_record.id,
                "filename": job_record.filename,
                "status": job_record.status,
                "created_at": job_record.created_at.isoformat() if job_record.created_at else None,
                "completed_at": job_record.completed_at.isoformat() if job_record.completed_at else None,
                "error_message": job_record.error_message,
                "quality_score": job_record.quality_score,
                "selected_ucs": job_record.selected_ucs
            }
            
            await websocket_manager.broadcast_job_update(job_data)
        except Exception as e:
            logger.error(f"Error broadcasting job update: {e}")
    
    async def _broadcast_stats_update(self):
        """Broadcast statistics updates via WebSocket"""
        try:
            from app.websocket_manager import websocket_manager
            from app.api.stats import get_statistics
            
            stats = await get_statistics()
            await websocket_manager.broadcast_stats_update(stats.dict())
        except Exception as e:
            logger.error(f"Error broadcasting stats update: {e}")
    
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
        
        # Run UC1 analysis with temp folder
        result = await run_uc1_analysis(
            file_path=str(csv_file),
            temp_folder=temp_folder,
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
        
        # Run UC4 analysis with temp folder
        result = await run_uc4_analysis(
            file_path=str(csv_file),
            temp_folder=temp_folder,
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
        1. Setup job folder structure (inputs/job_X, temp/job_X, outputs/job_X)
        2. Copy input file to job inputs folder
        3. Process file with selected use cases in temp folder
        4. Copy final result to outputs folder
        5. Store results in database
        """
        logger.info(f"Starting job workflow for job {job_id} with use cases: {selected_use_cases}")
        
        # Get job record
        job_record = self.db.query(JobRecord).filter(JobRecord.id == job_id).first()
        if not job_record:
            raise ValueError(f"Job {job_id} not found")
        
        # Check if original file exists
        original_file_path = Path(job_record.file_path)
        if not original_file_path.exists():
            raise FileNotFoundError(f"Input file not found: {original_file_path}")
        
        # Setup job folder structure
        job_structure = self.setup_job_folders(job_id)
        
        # Copy input file to job inputs folder
        job_input_file = job_structure.inputs_folder / original_file_path.name
        shutil.copy2(original_file_path, job_input_file)
        logger.info(f"Copied input file to job inputs: {job_input_file}")
        
        # Update job status to processing
        job_record.status = "processing"
        self.db.commit()
        
        # Broadcast job status update
        await self._broadcast_job_update(job_record)
        
        # Add a small delay to ensure the processing status is visible
        await asyncio.sleep(0.5)
        
        # Process each use case
        results = {}
        final_result = None
        current_input_file = job_input_file  # Start with the input file in job inputs folder
        input_folder_ = current_input_file.parent
        for use_case in selected_use_cases:
            logger.info(f"Processing use case: {use_case}")
            
            # Create use case temp folder
            uc_temp_folder = self.create_use_case_temp_folder(job_structure.temp_folder, use_case)
            
            # Update job record with current use case
            job_record.status = f"processing_{use_case.lower()}"
            self.db.commit()
            
            # Broadcast status update
            await self._broadcast_job_update(job_record)
            
            # Small delay to ensure status is visible
            await asyncio.sleep(0.2)
            output_dir_ = job_structure.temp_folder / use_case
            output_dir_.mkdir(exist_ok=True, parents=True)
            try:
                if use_case.lower() == "uc1":
                    # Process with UC1 agent
                    result = await asyncio.create_task(run_uc1_analysis(
                        file_path=str(current_input_file),
                        temp_folder=uc_temp_folder,
                        unique_filename=f"{current_input_file.stem}_{job_id}",
                        input_file_=input_folder_ / current_input_file.name,
                        output_dir_=output_dir_,
                    ))
                elif use_case.lower() == "uc4":
                    # Process with UC4 agent
                    result = await asyncio.create_task(run_uc4_analysis(
                        file_path=str(current_input_file),
                        temp_folder=uc_temp_folder,
                        unique_filename=f"{current_input_file.stem}_{job_id}",
                        input_file_=input_folder_ / current_input_file.name,
                        output_dir_=output_dir_,
                    ))
                else:
                    logger.error(f"Unknown use case: {use_case}")
                    continue
                
                results[use_case] = result
                final_result = result  # Keep last result as final
                
                # For next use case, use the output of this use case as input
                if hasattr(result, 'output_file_path') and result.output_file_path and Path(result.output_file_path).exists():
                    current_input_file = Path(result.output_file_path)
                    logger.info(f"Using output of {use_case} as input for next use case: {current_input_file}")
                
                logger.info(f"Successfully processed with {use_case}")
                
                # Update status after each use case completes
                job_record.status = f"completed_{use_case.lower()}"
                self.db.commit()
                await self._broadcast_job_update(job_record)
                await asyncio.sleep(0.1)  # Brief pause for status visibility
                
            except Exception as e:
                logger.error(f"Error processing with {use_case}: {str(e)}")
                job_record.status = "failed"
                job_record.error_message = str(e)
                job_record.completed_at = datetime.utcnow()
                self.db.commit()
                await self._broadcast_job_update(job_record)
                await self._broadcast_stats_update()
                raise
            input_folder_ = output_dir_
            shutil.rmtree(job_structure.outputs_folder)
            shutil.copytree(output_dir_, job_structure.outputs_folder, dirs_exist_ok=True)
        
        # Copy final result to outputs folder (only the last step output)
        if final_result and hasattr(final_result, 'output_file_path') and final_result.output_file_path:
            final_output_file = Path(final_result.output_file_path)
            if final_output_file.exists():
                outputs_final_file = job_structure.outputs_folder / f"final_{original_file_path.name}"
                # shutil.copy2(final_output_file, outputs_final_file)
                logger.info(f"Copied final result to outputs folder: {outputs_final_file}")
                
                # Update job record with final output path
                job_record.result_file_path = str(outputs_final_file)
        
        # Update job with final results and metrics
        if final_result:
            job_record.results = json.dumps({
                "output_file_path": job_record.result_file_path if hasattr(job_record, 'result_file_path') else "",
                "processing_details": str(results),
                "job_structure": {
                    "inputs_folder": str(job_structure.inputs_folder),
                    "temp_folder": str(job_structure.temp_folder),
                    "outputs_folder": str(job_structure.outputs_folder)
                }
            })
            
            # Update job metrics based on result type
            from app.services.agents.uc1 import UC1AnalysisResult
            from app.services.agents.uc4 import UC4AnalysisResult
            
            if isinstance(final_result, UC1AnalysisResult):
                job_record.quality_score = final_result.overall_quality_score
                job_record.is_sparse = final_result.incomplete_percentage > 20  # Consider >20% incomplete as sparse
                job_record.total_rows_processed = final_result.total_rows
                job_record.total_rows_original = final_result.total_rows
            elif isinstance(final_result, UC4AnalysisResult):
                job_record.has_duplicates = final_result.duplicate_percentage > 0
                job_record.duplicate_percentage = final_result.duplicate_percentage
                job_record.total_rows_original = final_result.total_rows_original
                job_record.total_rows_processed = final_result.total_rows_processed
                job_record.quality_score = final_result.quality_improvement_score
        
        # Update job status to completed
        job_record.status = "completed"
        job_record.completed_at = datetime.utcnow()
        self.db.commit()
        
        # Broadcast final job update and stats
        await self._broadcast_job_update(job_record)
        await self._broadcast_stats_update()
        
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
