import { JobStatistics } from '@/types/job';

interface DashboardProps {
  stats: JobStatistics;
}

export default function Dashboard({ stats }: DashboardProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
      {/* Total Jobs */}
      <div className="card hover:shadow-lg transition-shadow duration-200 bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-100 to-blue-200 rounded-xl flex items-center justify-center shadow-sm">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-blue-700">Total Jobs</p>
            <p className="text-2xl font-semibold text-blue-900">{stats.total_jobs}</p>
          </div>
        </div>
      </div>

      {/* Pending Jobs */}
      <div className="card hover:shadow-lg transition-shadow duration-200 bg-gradient-to-br from-amber-50 to-amber-100 border-amber-200">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-gradient-to-br from-amber-100 to-amber-200 rounded-xl flex items-center justify-center shadow-sm">
              <svg className="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-amber-700">Pending</p>
            <p className="text-2xl font-semibold text-amber-900">{stats.pending_jobs}</p>
          </div>
        </div>
      </div>

      {/* Processing Jobs */}
      <div className="card hover:shadow-lg transition-shadow duration-200 bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-100 to-purple-200 rounded-xl flex items-center justify-center shadow-sm">
              <svg className={`w-6 h-6 text-purple-600 ${stats.processing_jobs > 0 ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </div>
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-purple-700">Processing</p>
            <p className="text-2xl font-semibold text-purple-900">{stats.processing_jobs}</p>
          </div>
        </div>
      </div>

      {/* Completed Jobs */}
      <div className="card hover:shadow-lg transition-shadow duration-200 bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-gradient-to-br from-emerald-100 to-emerald-200 rounded-xl flex items-center justify-center shadow-sm">
              <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-emerald-700">Completed</p>
            <p className="text-2xl font-semibold text-emerald-900">{stats.completed_jobs}</p>
          </div>
        </div>
      </div>

      {/* Failed Jobs */}
      <div className="card hover:shadow-lg transition-shadow duration-200 bg-gradient-to-br from-red-50 to-red-100 border-red-200">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-gradient-to-br from-red-100 to-red-200 rounded-xl flex items-center justify-center shadow-sm">
              <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-red-700">Failed</p>
            <p className="text-2xl font-semibold text-red-900">{stats.failed_jobs}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
