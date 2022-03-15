import React from "react";
import Form from "./form/form";
import Info from "./info/info";
import Weather from "./weather/weather";
import axios from "axios";
import'./../App.scss';

const API_KEY = 'd1812ab7b9819ec4f4e4bbd3f4a04ded';

class GetWeather extends React.Component {

  state = {
    city: null,
    country: null,
    temp: null,
    feelsLike: null,
    weather: null,
    update_at: null,
    error: ''
  };

  getWeather = async (event) => {
    event.preventDefault();
    var city = event.target.elements.city.value;
    
    if (city) {
      var today = new Date();
      const response = await axios.get(`http://localhost:8000/api/check-city/${city.toLowerCase()}`);

      if (response.data.status === 200) {
        let data = response.data.data;

        var nowDate = today.toISOString().replace(/\D/g,'').slice(0, -5);
        var updateDate = data.update_at.replace(/\D/g,'').slice(0, -5);
        var difference = Number.parseInt(nowDate) - Number.parseInt(updateDate);

        /*console.log(data);
        console.log(updateDate);
        console.log(nowDate);
        console.log(difference);*/


        if (difference > 30) {
          const API_URL = await fetch(`https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${API_KEY}&units=metric`);

          if(API_URL.ok)
          {
            const data = await API_URL.json();
            console.log(data);
              this.setState({
                city: data.name,
                country: data.sys.country,
                temp: data.main.temp,
                feelsLike: data.main.feels_like,
                pressure: data.main.pressure,
                weather: data.weather[0].main,
                update_at: today.toISOString(), 
                error: ''
              });
            }

          axios
          .put(`http://localhost:8000/api/update/${city.toLowerCase()}`, {
                city: this.state.city.toLowerCase(),
                country: this.state.country,
                temperature: this.state.temp,
                fellslike: this.state.feelsLike,
                pressure: this.state.pressure,
                weather: this.state.weather,
                update_at: this.state.update_at
                }).then(response => {
                  console.log(response.data.message); 
                })
                .catch(err => {
                  console.log(err);
                })
          
        }

        else {
          this.setState({
            city: data.city,
            country: data.country,
            temp: data.temperature,
            feelsLike: data.fellslike,
            pressure: data.pressure,
            weather: data.weather,
            error: ''
          }); 
        }
      }
      
      else {
      console.log("B");
      const API_URL = await fetch(`https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${API_KEY}&units=metric`);
      
      if(API_URL.ok)
      {
        const data = await API_URL.json();
        console.log(data);
              this.setState({
                city: data.name,
                country: data.sys.country,
                temp: data.main.temp,
                feelsLike: data.main.feels_like,
                pressure: data.main.pressure,
                weather: data.weather[0].main,
                update_at: today.toISOString(), 
                error: ''
              });
              axios
              .post("http://localhost:8000/api/save-weather", {
                city: this.state.city.toLowerCase(),
                country: this.state.country,
                temperature: this.state.temp,
                fellslike: this.state.feelsLike,
                pressure: this.state.pressure,
                weather: this.state.weather,
                update_at: this.state.update_at
                }).then(response => {
                  console.log(response.data.message); 
                })
        }
        else {
          this.setState({
            city: null,
            country: null,
            temp: null,
            feelsLike: null,
            weather: null,
            error: 'Такой город не найден'
        })
      }
    }
    } else {
      this.setState({
        city: null,
        country: null,
        temp: null,
        feelsLike: null,
        weather: null,
        error: 'Вы не набрали город'
      });
    }
  }



  render() {
    const {city, country, temp, feelsLike, pressure, weather, error} = this.state
    localStorage.clear();
    return (
      <div className='App-weather'>
        <Info city={city}/>
        <Form weatherMethod={this.getWeather}/>
        <Weather
          city={city}
          country={country}
          temp={temp}
          feelsLike={feelsLike}
          pressure={pressure}
          weather={weather}
          error={error}
        />
      </div> 
    )
  }
};

export default GetWeather;