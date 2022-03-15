import './weather.scss';

const Weather = ({city, weather, country, temp, feelsLike, pressure, error}) => (
    <div className='weather'>
        { city && 
            <div className='weather-data'>
            <div className='weather-data_item'>
                <div className='weather-value'>{weather}</div>
                <div className='string'>
                    <p className='variable'>Место:</p><p className='value'>{city}</p>
                </div>
                <div className='string'>
                    <p className='variable'>Государство:</p><p className='value'>{country}</p>
                </div>
            </div>
            <div className='weather-data_item'>
                <div className='string'>
                    <p className='variable'>Температура:</p><p className='value'>{Math.round(temp)} °C</p>
                </div>
                <div className='string'>
                    <p className='variable'>Ощущается как:</p><p className='value'>{Math.round(feelsLike)} °C</p>
                </div>
            </div>
            <div className='weather-data_item'>
                <div className='string'>
                    <p className='variable'>Давление:</p><p className='value'>{pressure} mbar</p>
                </div>
            </div>
    </div>
        }
        { error &&
            <p className='error'>Ошибка: {error}</p>
        }
    </div>
)

export default Weather;