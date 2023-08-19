import React, { useState } from 'react';
import axios from 'axios'; 
import './App.css';

function App() {
  const [isLoading, setIsLoading] = useState(false); //this is for when to display "loading.."
  const [csvData, setCsvData] = useState('');
  
  const handleGenerateReport = async () => {
    setIsLoading(true);
    setCsvData(''); // to clear the  previous CSV data
    try {
      // Trigger report generation
      const triggerResponse = await axios.get('http://localhost:5000/trigger_report');
      const reportId = triggerResponse.data.report_id;

      // Poll for report status until it's complete
      let status = 'Running';
      while (status === 'Running') {
        const get_status_response = await axios.get(`http://localhost:5000/get_report?report_id=${reportId}`);
        status = get_status_response.data.status;
      }
      // we need to get the report data when status is complete
      const get_report_response = await axios.get(`http://localhost:5000/get_report?report_id=${reportId}`);
      const reportData = get_report_response.data.csv_data;

      // this func is to convert reportData (JSON) to CSV format, since report data is in Json format
      const csvFormattedData = convertJSONToCSV(reportData);
      setCsvData(csvFormattedData);  // Update the state
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  };


  // Function to convert JSON to CSV format
  const convertJSONToCSV = (jsonArray) => {
    if (jsonArray.length === 0) {
      return '';
    }
    const keys = Object.keys(jsonArray[0]);
    const csvHeader = keys.join(',');
    const csvRows = jsonArray.map(obj => keys.map(key => obj[key]).join(','));
    return [csvHeader, ...csvRows].join('\n');
  };

  return (
    <div>
      <button onClick={handleGenerateReport} disabled={isLoading}>
        {isLoading ? 'Loading...' : 'Generate Report'}
      </button>
      <div className="table-container">
        <table className="csv-table">
          <tbody>
            {csvData.split('\n').map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.split(',').map((cell, cellIndex) => (
                  <td key={cellIndex}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
export default App;
