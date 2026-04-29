import { Cloud, Search, X } from 'lucide-react';

export default function ToolIndicator({ toolState }) {
  if (!toolState) return null;

  const { type, status, data } = toolState;
  const isWeather = type === 'weather';
  const isLoading = status === 'loading';

  return (
    <div className="tool-indicator-wrap">
      {/* Status pill */}
      <div className={`tool-pill ${isLoading ? 'tool-pill-loading' : 'tool-pill-done'}`}>
        {isWeather ? <Cloud size={12} className="inline mr-1" /> : <Search size={12} className="inline mr-1" />}
        {isLoading
          ? isWeather ? 'Checking weather...' : 'Searching...'
          : isWeather ? 'Weather result' : 'Search result'}
      </div>

      {/* Result card */}
      {!isLoading && data && (
        <div className="tool-result-card">
          {isWeather ? (
            <div className="tool-weather">
              <span className="tool-weather-city">{data.city}</span>
              <span className="tool-weather-temp">{data.temperature}{data.unit}</span>
              <span className="tool-weather-cond">{data.condition}</span>
              {data.humidity && <span className="tool-weather-extra">💧 {data.humidity}%  💨 {data.windspeed} km/h</span>}
            </div>
          ) : (
            <div className="tool-search">
              {data.answer && <p className="tool-search-answer">{data.answer}</p>}
              {data.results?.length > 0 && (
                <ul className="tool-search-links">
                  {data.results.slice(0, 3).map((r, i) => (
                    <li key={i}>
                      <a href={r.url} target="_blank" rel="noreferrer" className="tool-search-link">
                        {r.text.slice(0, 80)}{r.text.length > 80 ? '…' : ''}
                      </a>
                    </li>
                  ))}
                </ul>
              )}
              {!data.answer && !data.results?.length && (
                <p className="tool-search-empty">No instant answer found.</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
