import { useState, useEffect, useContext } from "react";
import axios from "axios";
import { UserContext } from '../../index';
import './FutureWeather.scss'

function FutureWeather({ cityData }) {
  const baseURL = 'http://localhost:8000/api'
  const [futureWeather, setFutureWeather] = useState({
    calendar_date: Array(7).fill('date'),
    min_temperature: Array(7).fill(3),
    max_temperature: Array(7).fill(13),
    precipitation: Array(7).fill(0)
  })
 
  const [isLoading, setLoading] = useState(false);
  const { isdisable, setDisable } = useContext(UserContext);

  useEffect(() => {
    async function getWeeklyForecast() {
      try {
        const urlParams = new URLSearchParams({
          lat: cityData.lat, lng: cityData.lng
        })
        var resTempForecast = await axios.get(
          `${baseURL}/forecast?${urlParams}`
        )  
        setFutureWeather(resTempForecast.data)
        setLoading(true)
        setDisable(false)
      } catch(error) {
        console.log(error)
      }
    }
    getWeeklyForecast()
  }, [cityData.lat, cityData.lng])

  return (
    <> {isLoading ?
    <div className="weather-future">
      { [...Array(7).keys()].map((ind) => { return (
          <div className="weather-future-tile" key={ind.toString()}>
            <div className="weather-future-tile-date">
              {futureWeather.calendar_date[ind]}
            </div>
            <div className="weather-future-tile-item">
              <span className="weather-future-tile-item-maxtemp">
                {
                  futureWeather.max_temperature[ind] > 0
                  ? '+' + futureWeather.max_temperature[ind]
                  : futureWeather.max_temperature[ind]
                }
              </span>
                {
                  futureWeather.precipitation[ind] > 50
                  ? <>
                    { (futureWeather.max_temperature < 3 && 
                      futureWeather.max_temperature > -1) || 
                      (futureWeather.min_temperature < 3 &&
                      futureWeather.min_temperature > -1) 
                      ? 
                        <div className="weather-future-tile-item-icon-snowing"/>
                      : <> 
                      { (futureWeather.max_temperature <= -1 && 
                        futureWeather.min_temperature <= -1) 
                        ?
                          <div className="weather-future-tile-item-icon-snow"/>
                        :
                          <div className="weather-future-tile-item-icon-rain"/>
                      } </>
                    } </>
                  : <div className="weather-future-tile-item-icon-sunny"></div>
                }
            </div>

            <div className="weather-future-tile-item">
              <span className="weather-future-tile-mintemp">
                {
                  futureWeather.min_temperature[ind] > 0
                  ? '+' + futureWeather.min_temperature[ind]
                  : futureWeather.min_temperature[ind]
                }
              </span>
              <span className="weather-future-tile-precip">
                {futureWeather.precipitation[ind]}%
              </span>
            </div>

          </div>
        )} )
      } 
    </div>
    : 
    <div style={{marginTop: '1rem'}}>
      <span>Please wait while the weekly forecast is being formed  </span>   
      <span
        className="spinner-border spinner-border-sm ml-5"
        role="status"
        aria-hidden="true">
      </span> 
    </div>}
    </>
  )
}

export default FutureWeather;