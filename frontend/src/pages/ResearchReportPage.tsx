import React from 'react';
import { FileText } from 'lucide-react';
import { EmptyState } from '../components/ui/EmptyState';
import { Badge } from '../components/ui/Badge';

export const ResearchReportPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-[#111722] border border-[#232E42] rounded-lg p-5 flex items-center justify-between shadow-xl">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base font-bold font-mono text-white">Institutional Research Report</h1>
              <Badge variant="cyan" size="xs">Phase 13 Target</Badge>
            </div>
            <p className="text-xs text-slate-400">
              Generate institutional-grade tear sheets, strategy teardowns, and multi-asset research dossiers.
            </p>
          </div>
        </div>
      </div>

      <EmptyState
        title="Research Report Generator"
        description="The Research Report Generator will be implemented in Phase 13. It synthesizes quantitative indicators, correlation shifts, backtest results, and regime diagnostics into an exportable research tear sheet."
        phase={13}
        icon={<FileText className="w-7 h-7 text-cyan-400" />}
        details={[
          'Comprehensive Executive Tear Sheet Summary',
          'Automated Risk / Return Factsheet',
          'PDF & Markdown Export Capabilities',
          'Hackathon Presentation Mode & Demonstration Suite'
        ]}
      />
    </div>
  );
};
