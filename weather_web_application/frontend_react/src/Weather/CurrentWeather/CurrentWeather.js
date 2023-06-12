import { useState, useEffect } from 'react';
import './CurrentWeather.scss';
import axios from 'axios';

function CurrentWeather({ cityData }) {

  const API_KEY = 'd1812ab7b9819ec4f4e4bbd3f4a04ded';
  const baseURL = 'http://localhost:8000/api';
  const [isLoading, setLoading] = useState(false);

  const [weatherData, setWeatherData] = useState({
    calendar_date: null,
    temperature: 1,
    feels_like: 3,
    weather_condition: 'Sleet',
    pressure: 760,
    humidity: 50,
    wind_speed: 3,
    wind_direction: 0, 
    sunrise: '6:10:34',
    sunset: '20:10:42',
    updated_at: null
  })

  useEffect(() => {
    async function getCurrentWeatherData() {

      const makeRequest = async (method, url) => {
          const res1 = await axios.get(
            `https://api.openweathermap.org/data/2.5/weather?` + 
            `lat=${cityData.lat}&lon=${cityData.lng}&` + 
            `appid=${API_KEY}&units=metric`
          )
          const currentWeatherData = res1.data
          const currentDate = new Date()
          const calendarDate = currentDate.toISOString().split('T')[0]
          const dateTime = currentDate.toISOString()

          const unixTimes = [
            currentWeatherData.sys.sunrise, currentWeatherData.sys.sunset
          ]

          const [sunrise, sunset] = unixTimes.map(
            t => new Date(t*1000).toTimeString().split(' ')[0]
          )

          const newWeatherData = {
            calendar_date: calendarDate,
            temperature: parseInt(currentWeatherData.main.temp),
            feels_like: parseInt(currentWeatherData.main.feels_like),
            weather_condition: currentWeatherData.weather[0].main,
            pressure: parseInt(currentWeatherData.main.pressure),
            humidity: parseInt(currentWeatherData.main.humidity),
            wind_speed: parseInt(currentWeatherData.wind.speed),
            wind_direction: parseInt(currentWeatherData.wind.deg), 
            sunrise: sunrise,
            sunset: sunset,
            updated_at: dateTime
          }

          setWeatherData(newWeatherData)

          var data = {...{city: cityData.id}, ...newWeatherData}
          axios({method, url, data})
        }

      // At first we try to find the weather data in a database
      let isThereDataInDB = true
      try {
        var resCity = await axios.get(
          `${baseURL}/current-weather/${cityData.id}/`
        )
      } catch(error) {
        console.log(error)
        isThereDataInDB = false
      }

      // if there are data in a database
      if (isThereDataInDB) {
        const dbWeatherdata = resCity.data;
        console.log(dbWeatherdata)
        let currentDatetime = new Date()
        let minuteDiff = Math.floor(
          (currentDatetime - new Date(dbWeatherdata.updated_at)) / 60000
        );

        // If 30 minutes have passed, then we update the values
        if (minuteDiff < 30) {
          setWeatherData(dbWeatherdata)
        }
        else {
          makeRequest('put', `${baseURL}/current-weather/${cityData.id}/`)
        }
      }
      else {
        makeRequest('post', `${baseURL}/current-weather/`)
      }
    }
    getCurrentWeatherData()
    setLoading(true)
  }, [cityData.id, cityData.lat, cityData.lng]) 

  // Turning 0-360 into 0-8, rounding to ensure a whole number to use an index
  const convertDegreesToWindDirection = (degrees) => {
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    // Split into the 8 directions
    degrees = degrees * 8 / 360;
    // round to nearest integer.
    degrees = Math.round(degrees, 0);
    // Ensure it's within 0-7
    degrees = (degrees + 8) % 8
    return directions[degrees] 
  }

  const renderWeatherIcon = weatherCondition => {
    weatherCondition = weatherCondition.toLowerCase()
    if (weatherCondition.includes('rain')) {
      return <div className='weather-current-temp-icon-rain'/>
    }
    else if (weatherCondition.includes('snow')) {
      return <div className='weather-current-temp-icon-snow'/>
    }
    else if (weatherCondition.includes('sleet')) {
      return <div className='weather-current-temp-icon-snowing'/>
    }
    else if (weatherCondition.includes('hail')) {
      return <div className='weather-current-temp-icon-hail'/>
    }
    else {
      return <div className='weather-current-temp-icon-sunny'/>
    }
  }

  return ( 
    <> {isLoading ?   
      <div className='weather-current'>

        <div className='weather-current-temp'>
          { 
            weatherData.temperature > 0 
            ? '+' + weatherData.temperature 
            : weatherData.temperature
          }
          <span className='weather-current-temp-grad'>°</span>
          { renderWeatherIcon(weatherData.weather_condition) }
        </div>


        <div className='weather-current-data'>
          <div className='weather-current-data-list'>

            <div className='weather-current-data-item'>
              <span className='weather-current-data-title'>
                {weatherData.weather_condition}
              </span>
            </div>

            <div className='weather-current-data-item'>
              <span className='weather-current-data-title'>
                Wind 
              </span>
              <span className='weather-current-data-value'>
                {
                  convertDegreesToWindDirection(weatherData.wind_direction) +
                  ' ' + weatherData.wind_speed
                } m/s
              </span>
            </div>

            <div className='weather-current-data-item'>
              <span className='weather-current-data-title'>
                Sunrise
              </span>
              <span className='weather-current-data-value'>
                {weatherData.sunrise.slice(0, -3)}
              </span>
            </div>

            <div className='weather-current-data-item'>
              <span className='weather-current-data-title'>
                Sunset
              </span>
              <span className='weather-current-data-value'>
                {weatherData.sunset.slice(0, -3)}
              </span>
            </div>

          </div>
          <div className='weather-current-data-list'>

            <div className='weather-current-data-item'>
              <span className='weather-current-data-title'>
                Feels like 
              </span>
              <span className='weather-current-data-value'>
                {
                  weatherData.feels_like > 0 
                  ? '+' + weatherData.feels_like 
                  : weatherData.feels_like
                }°
              </span>
            </div>

            <div className='weather-current-data-item'>
              <span className='weather-current-data-title'>
                Humidity
              </span>
              <span className='weather-current-data-value'>
                {weatherData.humidity}%
              </span>
            </div>
            
            <div className='weather-current-data-item'>
              <span className='weather-current-data-title'>
                Pressure
              </span>
              <span className='weather-current-data-value'>
                {weatherData.pressure} hPa
              </span>
            </div>

          </div>
        </div>
      </div>
    : 
      <div style={{marginBottom: '1rem'}}> 
        <span
          className="spinner-border spinner-border-sm ml-5"
          role="status"
          aria-hidden="true">
        </span> 
      </div>}
    </>
  )
}

export default CurrentWeather;