import { useEffect, useState } from 'react';
import { useStore } from '../../store/useStore';
import { api } from '../../services/api';
import { Database, AlertTriangle } from 'lucide-react';

export const DatabaseTables = () => {
  const { tables, setTables, activeTableData, setActiveTableData } = useStore();
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [columns, setColumns] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTables = async () => {
      setLoading(true);
      setError(null);
      const data = await api.get('/tables');
      if (data && data.tables) {
        setTables(data.tables.map((t: any) => t.name));
      } else {
        setError('Failed to fetch tables from backend');
        setTables([]);
      }
      setLoading(false);
    };
    fetchTables();
  }, [setTables]);

  const handleSelectTable = async (tableName: string) => {
    setSelectedTable(tableName);
    setLoading(true);
    setError(null);
    const data = await api.get(`/tables/${tableName}`);
    if (data && data.columns && data.rows) {
      setColumns(data.columns.map((c: any) => c.name));
      setActiveTableData(data.rows);
    } else {
      setError(`Failed to fetch data for table: ${tableName}`);
      setColumns([]);
      setActiveTableData([]);
    }
    setLoading(false);
  };

  return (
    <div style={{ height: '300px', backgroundColor: '#1a1a1a', borderTop: '2px solid #333', color: 'white', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '10px 20px', borderBottom: '1px solid #333', display: 'flex', gap: '10px', alignItems: 'center' }}>
        <Database size={18} color="#4caf50" />
        <strong style={{ marginRight: '20px' }}>Database Tables:</strong>
        <div style={{ display: 'flex', gap: '10px', overflowX: 'auto' }}>
          {tables.map(t => (
            <button 
              key={t}
              onClick={() => handleSelectTable(t)}
              style={{ padding: '5px 15px', backgroundColor: selectedTable === t ? '#4caf50' : '#333', border: 'none', borderRadius: '4px', color: 'white', cursor: 'pointer' }}
            >
              {t}
            </button>
          ))}
        </div>
      </div>
      <div style={{ flex: 1, overflow: 'auto', padding: '20px' }}>
        {loading && <div style={{ color: '#888' }}>Loading table data...</div>}
        
        {error && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#ff6b6b', marginBottom: '10px' }}>
            <AlertTriangle size={18} />
            <span>{error}</span>
          </div>
        )}

        {!loading && !selectedTable && (
          <div style={{ color: '#888' }}>Select a table to view its contents.</div>
        )}

        {!loading && selectedTable && columns.length === 0 && (
          <div style={{ color: '#888' }}>No columns defined for this table.</div>
        )}

        {!loading && selectedTable && columns.length > 0 && (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #444' }}>
                {columns.map(colName => (
                  <th key={colName} style={{ padding: '10px', textAlign: 'left', color: '#aaa' }}>{colName}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {activeTableData.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} style={{ padding: '20px', textAlign: 'center', color: '#888' }}>
                    Table is empty
                  </td>
                </tr>
              ) : (
                activeTableData.map((row, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #333' }}>
                    {columns.map(colName => (
                      <td key={colName} style={{ padding: '10px' }}>
                        {row[colName] !== undefined && row[colName] !== null ? String(row[colName]) : ''}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
