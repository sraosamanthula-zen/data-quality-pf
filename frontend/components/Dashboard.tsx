import { JobStatistics } from '@/types/job';

interface DashboardProps {
  stats: JobStatistics;
}

export default function Dashboard({ stats }: DashboardProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
      {/* Total Jobs */}
      <div className="card hover:shadow-lg transition-shadow duration-200 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 border-blue-200 dark:border-blue-700 theme-transition">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-100 to-blue-200 dark:from-blue-800 dark:to-blue-700 rounded-xl flex items-center justify-center shadow-sm theme-transition">
              <svg className="w-6 h-6 text-blue-600 dark:text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-blue-700 dark:text-blue-300 theme-transition">Total Jobs</p>
            <p className="text-2xl font-semibold text-blue-900 dark:text-blue-100 theme-transition">{stats.total_jobs}</p>
          </div>
        </div>
      </div>

      {/* Pending Jobs */}
      <div className="card hover:shadow-lg transition-shadow duration-200 bg-gradient-to-br from-amber-50 to-amber-100 dark:from-amber-900/30 dark:to-amber-800/30 border-amber-200 dark:border-amber-700 theme-transition">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-gradient-to-br from-amber-100 to-amber-200 dark:from-amber-800 dark:to-amber-700 rounded-xl flex items-center justify-center shadow-sm theme-transition">
              <svg className="w-6 h-6 text-amber-600 dark:text-amber-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-amber-700 dark:text-amber-300 theme-transition">Pending</p>
            <p className="text-2xl font-semibold text-amber-900 dark:text-amber-100 theme-transition">{stats.pending_jobs}</p>
          </div>
        </div>
      </div>

      {/* Processing Jobs */}
      <div className="card hover:shadow-lg transition-shadow duration-200 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/30 dark:to-purple-800/30 border-purple-200 dark:border-purple-700 theme-transition">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-100 to-purple-200 dark:from-purple-800 dark:to-purple-700 rounded-xl flex items-center justify-center shadow-sm theme-transition">
              <svg className={`w-6 h-6 text-purple-600 dark:text-purple-300 ${stats.processing_jobs > 0 ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </div>
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-purple-700 dark:text-purple-300 theme-transition">Processing</p>
            <p className="text-2xl font-semibold text-purple-900 dark:text-purple-100 theme-transition">{stats.processing_jobs}</p>
          </div>
        </div>
      </div>

      {/* Completed Jobs */}
      <div className="card hover:shadow-lg transition-shadow duration-200 bg-gradient-to-br from-emerald-50 to-emerald-100 dark:from-emerald-900/30 dark:to-emerald-800/30 border-emerald-200 dark:border-emerald-700 theme-transition">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-gradient-to-br from-emerald-100 to-emerald-200 dark:from-emerald-800 dark:to-emerald-700 rounded-xl flex items-center justify-center shadow-sm theme-transition">
              <svg className="w-6 h-6 text-emerald-600 dark:text-emerald-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-emerald-700 dark:text-emerald-300 theme-transition">Completed</p>
            <p className="text-2xl font-semibold text-emerald-900 dark:text-emerald-100 theme-transition">{stats.completed_jobs}</p>
          </div>
        </div>
      </div>

      {/* Failed Jobs */}
      <div className="card hover:shadow-lg transition-shadow duration-200 bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/30 dark:to-red-800/30 border-red-200 dark:border-red-700 theme-transition">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-gradient-to-br from-red-100 to-red-200 dark:from-red-800 dark:to-red-700 rounded-xl flex items-center justify-center shadow-sm theme-transition">
              <svg className="w-6 h-6 text-red-600 dark:text-red-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-red-700 dark:text-red-300 theme-transition">Failed</p>
            <p className="text-2xl font-semibold text-red-900 dark:text-red-100 theme-transition">{stats.failed_jobs}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
