export interface Job {
  id: number;
  filename: string;
  file_path: string;
  job_type: string;
  selected_ucs?: string[];
  is_reference?: boolean;
  reference_file_id?: number;
  sparse_compared_to_reference?: boolean;
  status: 'uploaded' | 'pending' | 'queued' | 'processing' | 'processing_uc1' | 'processing_uc4' | 'analyzing_completeness' | 'analysis_complete' | 'detecting_duplicates' | 'cleaning_file' | 'cleaning_complete' | 'completed' | 'failed' | 'analysis_complete_with_warnings' | 'cleaning_failed';
  created_at: string;
  started_at?: string;
  completed_at?: string;
  is_sparse?: boolean;
  has_duplicates?: boolean;
  error_message?: string;
}

export interface JobDetails extends Job {
  results: any;
}

export interface JobStatistics {
  total_jobs: number;
  pending_jobs: number;
  processing_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
}

export interface UploadResponse {
  job_id: number;
  message: string;
  filename: string;
  job_type: string;
}
