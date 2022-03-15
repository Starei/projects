
import React from "react";
import { Switch, Route } from 'react-router-dom';
import Header from './Header/Header';
import AddMessage from "./Sign/AddMessage";
import GetWeather from './Weather/GetWeather';
import SignIn from './SignIn/SignIn';
import SignUp from './SignUp/SignUp';
import Users from "./Sign/Users";
import Message from "./Sign/Message";
import'./App.scss';

const App = (props) => {
  return (
    <div>
      <Header 
        login={props.login} 
        authorized={props.authorized}
        setAuthLogin={props.setAuthLogin} 
        setAuthStatus={props.setAuthStatus}
      />
      <div className='App'>
          <Switch>
              <Route exact path='/' component={GetWeather}/>
              <Route path='/sign-in' component={() => 
                <SignIn
                  setAuthLogin={props.setAuthLogin} 
                  setAuthStatus={props.setAuthStatus}
                />
              }/>
              <Route path='/sign-up' component={() => 
                <SignUp
                  setAuthLogin={props.setAuthLogin} 
                  setAuthStatus={props.setAuthStatus}  
                />}
              />
              <Route path='/users' component={Users}/>
              <Route path='/add' component={AddMessage}/>
              <Route path='/reports' component={Message}/>
          </Switch>
      </div>
    </div>
  );
}

export default App;