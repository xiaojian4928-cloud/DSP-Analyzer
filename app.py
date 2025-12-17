import React, { useState, useEffect, useMemo } from 'react';
import * as XLSX from 'xlsx'; // Import for library side effects if needed, though mostly used in utils
import { FileUpload } from './components/FileUpload';
import { Sidebar } from './components/Sidebar';
import { KPIGrid } from './components/KPIGrid';
import { DataTable } from './components/DataTable';
import { AnalysisChart } from './components/AnalysisChart';
import { ProcessedRow, FilterConfig } from './types';
import { aggregateData } from './utils/dataUtils';
import { Loader2 } from 'lucide-react';

// Initialize global script for tailwind
const App: React.FC = () => {
  const [rawData, setRawData] = useState<ProcessedRow[] | null>(null);
  const [config, setConfig] = useState<FilterConfig>({
    dateRange: ['', ''],
    dimensions: ['ADV Name', '日期']
  });

  // Calculate global min/max date when data loads
  useEffect(() => {
    if (rawData && rawData.length > 0) {
      const dates = rawData.map(r => r['日期']).sort();
      const min = dates[0];
      const max = dates[dates.length - 1];
      
      setConfig(prev => ({
        ...prev,
        dateRange: [min, max]
      }));
    }
  }, [rawData]);

  const aggregatedData = useMemo(() => {
    if (!rawData || !config.dateRange[0]) return [];
    return aggregateData(rawData, config.dimensions, config.dateRange);
  }, [rawData, config]);

  // Determine min/max dates for sidebar constraints
  const dateLimits = useMemo(() => {
    if (!rawData || rawData.length === 0) return { min: '', max: '' };
    const dates = rawData.map(r => r['日期']).sort();
    return { min: dates[0], max: dates[dates.length - 1] };
  }, [rawData]);

  if (!rawData) {
    return <FileUpload onDataLoaded={setRawData} />;
  }

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden font-sans text-slate-800">
      <Sidebar 
        config={config} 
        onConfigChange={setConfig} 
        minDate={dateLimits.min}
        maxDate={dateLimits.max}
      />
      
      <main className="flex-1 overflow-y-auto p-6 md:p-8">
        <div className="max-w-7xl mx-auto">
          <header className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Marketing Analytics</h1>
            <p className="text-gray-500 mt-1">Performance dashboard and metrics explorer</p>
          </header>

          {aggregatedData.length > 0 ? (
            <>
              <KPIGrid data={aggregatedData} />
              <DataTable data={aggregatedData} dimensions={config.dimensions} />
              <AnalysisChart data={aggregatedData} dimensions={config.dimensions} />
            </>
          ) : (
             <div className="flex flex-col items-center justify-center h-64 bg-white rounded-xl border border-gray-200 border-dashed">
                <Loader2 className="w-8 h-8 text-blue-500 animate-spin mb-2" />
                <p className="text-gray-500">Processing data or no records found for current range...</p>
             </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default App;
