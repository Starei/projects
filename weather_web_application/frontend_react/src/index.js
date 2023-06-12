import { React, createContext } from 'react';
import ReactDOM from 'react-dom/client';
import './Assets/index.scss';
import 'bootstrap/dist/css/bootstrap.min.css';
import App from './App';
import { BrowserRouter } from 'react-router-dom';


export const UserContext = createContext(null)
const root = ReactDOM.createRoot(document.getElementById('root'))

root.render(
  <BrowserRouter>
    <App />
  </BrowserRouter>,
);
