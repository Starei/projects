import { useEffect, useState, React } from "react";
import FutureWeather from "./FutureWeather/FutureWeather";
import CurrentWeather from "./CurrentWeather/CurrentWeather";
import { useLocation } from 'react-router-dom';
import'./Weather.scss';


function Weather () {
  const location = useLocation();
  const cityData = location.state.cityData;
  const [isLoading, setLoading] = useState(true);
  
  useEffect(() => {
    setTimeout(() => setLoading(false), 2000)
  }, [])

  return (
    <> { !isLoading ?
      <div className='weather'>
        <div className='weather-header'>
          <span>Weather {cityData.name}, {cityData.country}</span>
          <span>{new Date().toISOString().split('T')[0]}</span>
        </div>
          <CurrentWeather cityData={cityData} />
          <FutureWeather cityData={cityData} />
      </div>
      : <div className='weather'>
          <span
            className="spinner-border spinner-border-sm ml-5"
            role="status"
            aria-hidden="true">
          </span> 
        </div>
      }
    </>
  )
};

export default Weather;