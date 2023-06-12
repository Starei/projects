import React, { useState } from "react";
import { Routes, Route } from 'react-router-dom';
import Header from './Header/Header';
import Weather from './Weather/Weather';
import InputForm from "./InputForm/InputForm";
import { UserContext } from ".";
import'./Assets/App.scss';


const App = () => {
  const [disableSearchButton, setDisableSearchButton] = useState(true);

  return (
    <div>
      <UserContext.Provider 
        value={{
          isdisable: disableSearchButton,
          setDisable: setDisableSearchButton
        }}
      >
        <Header/>
        <div className='App'>
          <Routes>
            <Route exact path='/' element={<InputForm />}/>
            <Route path='/weather' element={<Weather />}/> 
          </Routes>
        </div>
      </UserContext.Provider>
    </div>
  );
}

export default App;