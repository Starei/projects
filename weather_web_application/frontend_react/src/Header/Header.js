import React, { useContext, useEffect } from 'react';
import { Link, useLocation } from "react-router-dom";
import { UserContext } from '..';
import './Header.scss';


function Header() { 
  const { isdisable, setDisable } = useContext(UserContext);
  const location = useLocation();

  useEffect(() => {
    if (location.pathname === '/') {
      setDisable(true);
    }
  })

  return (
  <header>
    <div className='header-wrapper'>
      <div className='header-wrapper-set'>
        {!isdisable
        ?
          <Link to='/' className='header-wrapper-set-button'>
            <p>Поиск</p>
          </Link>
        : 
          <span className='header-wrapper-set-button'>
            <p>Поиск</p>
          </span>
        }
      </div>
    </div>
  </header>
);
}
export default Header