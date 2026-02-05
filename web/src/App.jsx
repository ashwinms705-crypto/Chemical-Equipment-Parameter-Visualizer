import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line, Pie, Bar, Scatter } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

// Global Chart Defaults
ChartJS.defaults.color = '#94a3b8';
ChartJS.defaults.borderColor = '#334155';

function App() {
  const [file, setFile] = useState(null);
  const [data, setData] = useState(null);
  const [summary, setSummary] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await axios.get('/api/history/');
      // Ensure we always set an array
      setHistory(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      console.error("Failed to fetch history:", err);
    }
  };

  const handleDownloadReport = () => {
    axios.get('/api/report/', { responseType: 'blob' })
      .then((response) => {
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'report.pdf');
        document.body.appendChild(link);
        link.click();
      })
      .catch(err => alert("Failed to download report"));
  };

  const handleClear = async () => {
    if (window.confirm('Are you sure you want to clear all history?')) {
      try {
        await axios.post('/api/clear/');
        setHistory([]);
        setSummary(null);
        setData(null);
      } catch (err) {
        alert('Failed to clear history');
      }
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post('/api/upload/', formData);
      setSummary(res.data.summary);
      setData(res.data.data);
      fetchHistory();

      // Clear file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      setFile(null);
    } catch (err) {
      alert('Upload failed: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  const getChartData = () => {
    if (!data || data.length === 0) return { labels: [], datasets: [] };

    // Helper to find key case-insensitively
    const findKey = (obj, target) => {
      return Object.keys(obj).find(k => k.toLowerCase() === target.toLowerCase());
    };

    // Find keys in the first data point
    const flowKey = findKey(data[0], 'FlowRate') || findKey(data[0], 'Flow Rate') || 'FlowRate';
    const pressureKey = findKey(data[0], 'Pressure');
    const timeKey = findKey(data[0], 'Timestamp');

    const labels = data.map((d, i) => d[timeKey] || i);

    return {
      labels,
      datasets: [
        {
          label: 'Flow Rate',
          data: data.map(d => d[flowKey]),
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.5)',
          yAxisID: 'y',
        },
        {
          label: 'Pressure',
          data: data.map(d => d[pressureKey]),
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.5)',
          yAxisID: 'y1',
        },
      ],
    };
  };

  const getPieData = () => {
    if (!summary || !summary.equipment_distribution) return null;
    return {
      labels: Object.keys(summary.equipment_distribution),
      datasets: [
        {
          data: Object.values(summary.equipment_distribution),
          backgroundColor: [
            'rgba(59, 130, 246, 0.8)',
            'rgba(239, 68, 68, 0.8)',
            'rgba(16, 185, 129, 0.8)',
            'rgba(245, 158, 11, 0.8)',
            'rgba(139, 92, 246, 0.8)',
          ],
          borderColor: '#1e293b',
          borderWidth: 1,
        },
      ],
    };
  };

  // 2. Bar Chart - Flowrate by Equipment (Top 10 by Flow or all?)
  // Let's show all, but if too many, maybe limit or just use scroll.
  // 2. Bar Chart - Avg Flowrate by Equipment Type
  const getBarData = () => {
    if (!data || data.length === 0) return { labels: [], datasets: [] };

    // Helper to find key (reuse or redefine, better to hoist if possible, but local is fine)
    const findKey = (obj, target) => Object.keys(obj).find(k => k.toLowerCase() === target.toLowerCase());

    const typeKey = findKey(data[0], 'Type') || findKey(data[0], 'EquipmentType') || 'Type';
    const flowKey = findKey(data[0], 'FlowRate') || findKey(data[0], 'Flow Rate') || 'FlowRate';

    // Aggregate by Type
    const agg = {};
    data.forEach(d => {
      const type = d[typeKey] || 'Unknown';
      const flow = Number(d[flowKey]) || 0;

      if (!agg[type]) agg[type] = { sum: 0, count: 0 };
      agg[type].sum += flow;
      agg[type].count += 1;
    });

    const labels = Object.keys(agg);
    const flows = Object.values(agg).map(a => a.sum / a.count);

    return {
      labels,
      datasets: [{
        label: 'Avg Flowrate',
        data: flows,
        backgroundColor: [
          'rgba(59, 130, 246, 0.7)',
          'rgba(239, 68, 68, 0.7)',
          'rgba(16, 185, 129, 0.7)',
          'rgba(245, 158, 11, 0.7)',
          'rgba(139, 92, 246, 0.7)',
          'rgba(236, 72, 153, 0.7)'
        ],
        borderColor: '#3b82f6',
        borderWidth: 1
      }]
    };
  };

  // 4. Scatter - Flowrate vs Pressure
  const getScatterData = () => {
    if (!data || data.length === 0) return { datasets: [] };
    const findKey = (obj, target) => Object.keys(obj).find(k => k.toLowerCase() === target.toLowerCase());

    const flowKey = findKey(data[0], 'FlowRate') || 'FlowRate';
    const pressKey = findKey(data[0], 'Pressure') || 'Pressure';
    const typeKey = findKey(data[0], 'Type') || findKey(data[0], 'EquipmentType') || 'Type';

    // Group by Type for coloring
    const groups = {};
    data.forEach(d => {
      const type = d[typeKey] || 'Other';
      if (!groups[type]) groups[type] = [];
      groups[type].push({ x: d[flowKey], y: d[pressKey] });
    });

    const colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6'];

    return {
      datasets: Object.keys(groups).map((type, i) => ({
        label: type,
        data: groups[type],
        backgroundColor: colors[i % colors.length],
      }))
    };
  };

  // 5. Box Plot Proxy -> Scatter of Temp vs Type (Jittered?)
  // Using Scatter where X = Type (categorical mapped to num?), Y = Temp.
  // Actually, Chart.js Scatter needs numerical X. 
  // We can use a Bubble chart or just map Types to Indices 1, 2, 3...
  const getTempDistData = () => {
    if (!data || data.length === 0) return { datasets: [] };
    const findKey = (obj, target) => Object.keys(obj).find(k => k.toLowerCase() === target.toLowerCase());

    const tempKey = findKey(data[0], 'Temperature') || 'Temperature';
    const typeKey = findKey(data[0], 'Type') || 'Type';

    // Map types to indices
    const types = [...new Set(data.map(d => d[typeKey]))];
    const groups = {};

    data.forEach(d => {
      const type = d[typeKey] || 'Other';
      const typeIdx = types.indexOf(type);
      if (!groups[type]) groups[type] = [];
      // Add random jitter to X to spread points
      groups[type].push({ x: typeIdx + (Math.random() - 0.5) * 0.3, y: d[tempKey] });
    });

    const colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6'];

    return {
      datasets: Object.keys(groups).map((type, i) => ({
        label: type,
        data: groups[type],
        backgroundColor: colors[i % colors.length],
      }))
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    scales: {
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        title: {
          display: true,
          text: 'Flow Rate'
        },
        grid: {
          color: '#334155'
        },
        ticks: { color: '#94a3b8' }
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        title: {
          display: true,
          text: 'Pressure'
        },
        grid: {
          drawOnChartArea: false,
        },
        ticks: { color: '#94a3b8' }
      },
      x: {
        grid: {
          color: '#334155'
        },
        ticks: { color: '#94a3b8' }
      }
    },
    plugins: {
      legend: {
        labels: { color: '#cbd5e1' }
      }
    }
  };

  // Options for Temp chart to show Type Labels on X Axis
  const tempChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        type: 'linear',
        ticks: {
          callback: (val) => {
            // We need access to types here. Re-calculating for simplicity or state.
            if (!data) return '';
            const findKey = (obj, target) => Object.keys(obj).find(k => k.toLowerCase() === target.toLowerCase());
            const typeKey = findKey(data[0], 'Type') || 'Type';
            const types = [...new Set(data.map(d => d[typeKey]))];
            // Round val to nearest int
            const idx = Math.round(val);
            return types[idx] || '';
          },
          stepSize: 1
        },
        grid: { color: '#334155' }
      },
      y: {
        grid: { color: '#334155' },
        title: { display: true, text: 'Temperature' }
      }
    },
    plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => `Temp: ${ctx.raw.y}` } } }
  };


  return (
    <div className="container">
      <header>
        <h1>Chemical Equipment Parameter Visualizer</h1>
      </header>

      <div className="dashboard-grid">
        {/* Left Column: Upload, Charts, History */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

          {/* Upload Card */}
          <div className="card">
            <h2>Upload Data</h2>
            <form onSubmit={handleUpload}>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setFile(e.target.files[0])}
                ref={fileInputRef}
              />
              <div style={{ display: 'flex', gap: '10px' }}>
                <button className="btn" type="submit" disabled={loading}>
                  {loading && <span className="spinner"></span>}
                  {loading ? 'Processing...' : 'Analyze'}
                </button>
                <button className="btn" type="button" onClick={handleDownloadReport} style={{ backgroundColor: '#10b981' }}>
                  Download PDF
                </button>
              </div>
            </form>
          </div>

          {/* 1. Line Chart */}
          {data && (
            <div className="card">
              <h3>Parameter Trends (Flow & Pressure)</h3>
              <div style={{ height: '300px' }}>
                <Line options={chartOptions} data={getChartData()} />
              </div>
            </div>
          )}

          {/* New Charts Grid */}
          {data && (
            <div className="stat-grid">
              {/* 2. Bar Chart */}
              <div className="card" style={{ marginBottom: 0 }}>
                <h3>Avg Flow by Equipment</h3>
                <div style={{ height: '250px' }}>
                  <Bar options={{ responsive: true, maintainAspectRatio: false, scales: { y: { grid: { color: '#334155' } }, x: { grid: { display: false } } } }} data={getBarData()} />
                </div>
              </div>

              {/* 4. Scatter Flow vs Pressure */}
              <div className="card" style={{ marginBottom: 0 }}>
                <h3>Flowrate vs Pressure</h3>
                <div style={{ height: '250px' }}>
                  <Scatter options={{ responsive: true, maintainAspectRatio: false, scales: { y: { title: { display: true, text: 'Pressure' }, grid: { color: '#334155' } }, x: { title: { display: true, text: 'Flowrate' }, grid: { color: '#334155' } } } }} data={getScatterData()} />
                </div>
              </div>
            </div>
          )}

          {/* 5. Temp Distribution */}
          {data && (
            <div className="card">
              <h3>Temperature Variability by Type</h3>
              <div style={{ height: '300px' }}>
                <Scatter options={tempChartOptions} data={getTempDistData()} />
              </div>
            </div>
          )}

          {/* History */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ margin: 0 }}>Upload History</h2>
              <button onClick={handleClear} className="btn" style={{ backgroundColor: '#ef4444', padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}>Clear History</button>
            </div>
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Filename</th>
                  <th>Total Count</th>
                  <th>Avg Flow</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h, i) => (
                  <tr key={i}>
                    <td>{new Date(h.upload_date).toLocaleString()}</td>
                    <td>{h.filename}</td>
                    <td>{h.total_count}</td>
                    <td>{h.avg_flowrate.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: Sidebar Stats */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {summary && (
            <>
              <div className="card">
                <h2>Latest Summary</h2>
                <div className="stat-grid">
                  <div className="stat-box">
                    <div className="stat-label">Total Records</div>
                    <div className="stat-value">{summary.total_count}</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-label">Avg Flow</div>
                    <div className="stat-value">{summary.avg_flowrate.toFixed(2)}</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-label">Avg Pressure</div>
                    <div className="stat-value">{summary.avg_pressure.toFixed(2)}</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-label">Avg Temp</div>
                    <div className="stat-value">{summary.avg_temperature.toFixed(2)}</div>
                  </div>
                </div>
              </div>

              <div className="card">
                <h2>Equipment Distribution</h2>
                <div style={{ height: '220px', display: 'flex', justifyContent: 'center' }}>
                  {getPieData() && <Pie data={getPieData()} options={{ maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#cbd5e1', padding: 10, boxWidth: 12 } } } }} />}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
