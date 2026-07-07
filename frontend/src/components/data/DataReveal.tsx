import { ChevronUp, ChevronDown, Database, X } from 'lucide-react';
import { useStore } from '../../store/useStore';

export function DataReveal() {
  const {
    dataRevealOpen,
    tables,
    selectedTable,
    tableColumns,
    tableRows,
    tablesLoading,
    toggleDataReveal,
    closeDataReveal,
    selectTable,
    openDataReveal,
  } = useStore();

  if (tables.length === 0 && !tablesLoading) return null;

  const collapsedBar = (
    <button
      type="button"
      onClick={openDataReveal}
      className="flex w-full items-center justify-between rounded-2xl border border-outline-variant bg-surface px-4 py-3 shadow-sm transition-colors hover:bg-surface-container md:max-w-3xl md:mx-auto"
    >
      <div className="flex items-center gap-2">
        <Database size={18} className="text-primary" />
        <span className="text-sm font-medium text-on-surface">
          {selectedTable ? `Viewing: ${selectedTable}` : 'Your business data'}
        </span>
        {tables.length > 0 && (
          <span className="rounded-full bg-primary-container px-2 py-0.5 text-xs text-on-primary-container">
            {tables.length} {tables.length === 1 ? 'table' : 'tables'}
          </span>
        )}
      </div>
      <ChevronUp size={18} className="text-on-surface-variant" />
    </button>
  );

  return (
    <>
      <div className="hidden md:block absolute inset-x-0 bottom-24 z-10 px-4">
        {dataRevealOpen ? (
          <div className="mx-auto max-w-3xl animate-fade-in overflow-hidden rounded-2xl border border-outline-variant bg-surface shadow-lg">
            <DataPanel
              onClose={closeDataReveal}
              onCollapse={toggleDataReveal}
              expanded
            />
          </div>
        ) : (
          collapsedBar
        )}
      </div>

      <div className="md:hidden">
        {!dataRevealOpen && (
          <div className="absolute inset-x-0 bottom-24 z-10 px-4">{collapsedBar}</div>
        )}
        {dataRevealOpen && (
          <>
            <button
              type="button"
              className="fixed inset-0 z-30 bg-black/20"
              onClick={closeDataReveal}
              aria-label="Close data panel"
            />
            <div className="fixed inset-x-0 bottom-0 z-40 max-h-[70vh] animate-slide-up overflow-hidden rounded-t-3xl border-t border-outline-variant bg-surface shadow-2xl">
              <div className="flex justify-center py-2">
                <div className="h-1 w-10 rounded-full bg-outline" />
              </div>
              <DataPanel onClose={closeDataReveal} onCollapse={toggleDataReveal} expanded />
            </div>
          </>
        )}
      </div>
    </>
  );

  function DataPanel({
    onClose,
    onCollapse,
    expanded,
  }: {
    onClose: () => void;
    onCollapse: () => void;
    expanded: boolean;
  }) {
    return (
      <div className="flex max-h-[50vh] flex-col md:max-h-[320px]">
        <div className="flex items-center justify-between border-b border-outline-variant px-4 py-3">
          <div className="flex items-center gap-2">
            <Database size={18} className="text-primary" />
            <h3 className="text-sm font-semibold text-on-surface">Your data</h3>
          </div>
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={onCollapse}
              className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-surface-container"
              aria-label={expanded ? 'Collapse' : 'Expand'}
            >
              {expanded ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-surface-container md:hidden"
              aria-label="Close"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {tables.length > 0 && (
          <div className="flex gap-2 overflow-x-auto border-b border-outline-variant px-4 py-2">
            {tables.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => selectTable(t)}
                className={`shrink-0 rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
                  selectedTable === t
                    ? 'bg-primary text-on-primary'
                    : 'bg-surface-container text-on-surface-variant hover:bg-surface-container-high'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        )}

        <div className="flex-1 overflow-auto p-4">
          {tablesLoading && (
            <p className="text-sm text-on-surface-variant">Loading data…</p>
          )}
          {!tablesLoading && !selectedTable && (
            <p className="text-sm text-on-surface-variant">
              Select a table to view your records.
            </p>
          )}
          {!tablesLoading && selectedTable && tableColumns.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[400px] border-collapse text-sm">
                <thead>
                  <tr className="border-b border-outline-variant">
                    {tableColumns.map((col) => (
                      <th
                        key={col}
                        className="px-3 py-2 text-left text-xs font-medium text-on-surface-variant"
                      >
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {tableRows.length === 0 ? (
                    <tr>
                      <td
                        colSpan={tableColumns.length}
                        className="px-3 py-6 text-center text-on-surface-variant"
                      >
                        No records yet
                      </td>
                    </tr>
                  ) : (
                    tableRows.map((row, i) => (
                      <tr key={`${selectedTable}-${i}`} className="border-b border-outline-variant/50">
                        {tableColumns.map((col) => (
                          <td key={col} className="px-3 py-2 text-on-surface">
                            {row[col] != null ? String(row[col]) : '—'}
                          </td>
                        ))}
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    );
  }
}
