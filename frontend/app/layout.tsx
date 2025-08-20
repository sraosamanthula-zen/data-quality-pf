import '@/styles/globals.css'
import '@/styles/fixes.css'
import { Inter } from 'next/font/google'
import { ThemeProvider } from '@/contexts/ThemeContext'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'Agentic AI Data Quality Platform',
  description: 'AI-powered data quality platform for PnP data processing',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <ThemeProvider>
          <div className="min-h-screen bg-gray-50 dark:bg-gray-900 theme-transition">
            {children}
          </div>
        </ThemeProvider>
      </body>
    </html>
  )
}
