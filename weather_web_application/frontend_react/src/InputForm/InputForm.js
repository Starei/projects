import React, { useState, useEffect } from "react";
import { useNavigate } from 'react-router-dom';
import './InputForm.scss';
import axios from "axios";

function InputForm() {
  const [city, setCity] = useState('')
  const cleanCityInput = () => { setCity('') }

  const [coords, setCoords] = useState({
    lat: '',
    lng: ''
  })

  const [errors, setErrors] = useState({
    cityError: '',
    coordError: ''
  })

  const [redirect, setRedirect] = useState({
    state: false,
    cityData: {}
  })

  const navigate = useNavigate()
  const baseURL = 'http://localhost:8000/api'

  const [cities, setCities] = useState([
    // example demo 
    {city: 'Brest', country: 'Belarus'},  
    {city: 'Brest', country: 'France'}, 
  ])

  useEffect(() => {
    const fetchCityData = async () => {
      const resCities = await axios(`${baseURL}/city`);
      setCities(resCities.data)
    } 
    fetchCityData()
  }, []); // [] - This will run only once


  const handleChangeCoords = event => {
    // name is a property of input tag
    const { name, value } = event.target;
    setCoords(prevState => ({
      ...prevState,
      [name]: value
    }))
  }


  const cityRegex = new RegExp(/^[A-Za-z]+(?:[-\s][A-Za-z]+)*/)
  const countryRegex = new RegExp(/([\s]*,[\s]*[A-Za-z]+(?:[-\s][A-Za-z]+)*)*$/)
  const cityCountryregex = new RegExp(cityRegex.source + countryRegex.source)

  const validateCity = city => {
    city = city.trim()
    return !cityCountryregex.test(city)
    ? "Название города должно включать по меньшей мере одну букву. Название" +
    " может также содержать дефисы и пробелы. Когда необходимо, указывайте" +
    " страну через запятую: <название города>, <страна>. Так или иначе Вам" +
    " будет предложено выбрать пункт в случае, если городов с подобным" + 
    " названием окажется несколько."
    : "";
  }

  const cooordRegex = /^[0-9]+(\.[0-9]+)?$/

  const validateCoords = (lat, lng) => {
    return !(
      (cooordRegex.test(lat) && cooordRegex.test(lng)) &&
      (-90 <= parseFloat(lat) && parseFloat(lat) <= 90) && 
      (-180 <= parseFloat(lng) && parseFloat(lng) <= 180)
    )
    ? "Координаты, как правило, указываются в градусах. Широта в диапазоне" +
      " от -90 до 90, долгота - от -180 до 180]."
    : ""   
  }


  const onCityBlur = () => {
    const cityError = validateCity( city );
    if (cityError !== '' && city !== '') { alert(cityError) }
    return setErrors(previousState => {
      return { ...previousState, cityError }
    });
  };

  const onCoordsBlur = () => {
    const coordError = validateCoords( coords.lat, coords.lng );
    let filledFlag = Object.values(coords).every(Boolean)
    if (coordError !== '' && filledFlag) { alert(coordError) }  
    return setErrors(previousState => {
      return { ...previousState, coordError } 
    });
  }


  const checkCity = async (params) => {
    // convert an object in the required URL query format 
    const url_params = new URLSearchParams(params)
    try {
      const res = await axios.get(
        `${baseURL}/check-city?${url_params}`
      )
      const {status, message, cityData} = res.data
      if (status === 200) {
        if (message !== '') { 
          if (window.confirm(message) === false) { return } 
        }
        renderRedirect({
          id: cityData.id,
          name: cityData.name, 
          lat: cityData.lat, 
          lng: cityData.lng, 
          country: cityData.country
        })
      }
      else if (status === 202) {
        let number = 1
        let resMessage = "\n<Страна>: (<Широта>, <Долгота>)\n"
        for (const cityObject of cityData) {
          resMessage += (
            `${number}. ${cityObject['country']}: ` +
            `(${cityObject['lat']}, ${cityObject['lng']})\n`
          )
          number += 1
        }

        let numSelectedCity = prompt(message + resMessage)
        if (numSelectedCity === null) { return }
        const selectedCityData = cityData[numSelectedCity-1]
        renderRedirect({
          id: selectedCityData.id,
          name: selectedCityData.name, 
          lat: selectedCityData.lat, 
          lng: selectedCityData.lng, 
          country: selectedCityData.country
        })
      }
      else if (status === 404) { alert(message) }
    } catch (error) {
      alert("There is a problem with the operation on the server")
      console.log(error)
    }
  }

  const citySubmit = event => {
    event.preventDefault(); // prevent a browser reload/refresh
    if (errors.cityError === '') { checkCity({city: city}) }
    else { alert(errors.cityError) }
  }

  const coordSubmit = event => {
    event.preventDefault();
    if (errors.coordError === '') { checkCity(coords) }
    else { alert(errors.coordError) }
  }


  const renderRedirect = (cityData) => {
    setRedirect({
      state: true, 
      cityData: cityData 
    })
  }

  return (
    <div className="input_container">
      <div>
        {redirect.state &&
          navigate('/weather', {state: {cityData: redirect.cityData}})
        }
        <p>Введите координаты или название города</p>
      </div>
      <div className='input_form'>
        <form className="coord_form" onSubmit={coordSubmit}>
          <div className='coord_container'>

            <span className="coordinate">
              <span>Широта</span>
              <input 
                name='lat' // for handling changes
                type='text' 
                placeholder="Широта" 
                value={coords.lat} 
                onChange={handleChangeCoords}
                onBlur={onCoordsBlur}
                autoComplete="off"  
                required>
              </input>
            </span>

            <span className="coordinate">
              <span>Долгота</span>
              <input 
                name='lng'
                type='text' 
                placeholder="Долгота" 
                value={coords.lng} 
                onChange={handleChangeCoords} 
                onBlur={onCoordsBlur} 
                autoComplete="off"
                required>
              </input>
            </span>

          </div>
          <input
            id="button_coords"
            type="submit"
            className="button-coords"
            value=""
            >
          </input>
        </form>

        <form className="city_form" onSubmit={citySubmit}>
          <input
            type="reset"
            className="clear_button"
            value=""
            onClick={cleanCityInput}
          />
          <input 
            type='text' 
            name='city'
            list="cities" 
            placeholder='Поиск по городу'
            value={city}
            onFocus={(e) => e.target.placeholder = 'City[, country]'}
            onChange={(e) => setCity(e.target.value)}
            onBlur={onCityBlur}
            autoComplete="off"
            required
          />
          <datalist id="cities">
            { city.length > 2 && 
              cities.map(({name, country}, index) => {
                if ((name + country).toLowerCase().startsWith(
                  city.toLowerCase().replace(/[^a-z]+/g, '')
                ) && (
                  (name + country).toLowerCase() !== city.toLowerCase().replace(
                    /[^a-z]+/g, ''
                    )
                )
                ) { 
                  return <option key={index} value={name + ', ' + country}/> 
                }
              })
            }
          </datalist>
          <button type="submit">
            Найти
          </button>

        </form>
      </div>
    </div>
  )
}

export default InputForm;