import React from 'react';
import { Link } from "react-router-dom";
import './Header.scss';



function Header (props) { 
    
    const onLogoutHandler = () => {
        localStorage.clear();
        props.setAuthLogin('');
        props.setAuthStatus(false);
    };

    

    return (
    <header>
            <div className='header-wrapper'>
                    <div className='logo'>
                        <Link to='/' className='logo'>
                            <p>Погода</p>
                        </Link>
                        { props.authorized && <Link to='/reports' className='logo'> 
                            <p className='message'>Сообщения</p>
                        </Link>
                        }
                        {props.login === 'admin@mail.ru' &&
                        <span className='logo'>
                            <Link to='/users' className='logo'> 
                                <p className='message'>Пользователи</p>
                            </Link> 
                            <Link to='/add' className='logo'> 
                                <p className='message'>Сообщение</p>
                            </Link> 
                        </span>
                        }   
                    </div>
                <div className='info'>
                    <p className='login'>{props.authorized ? props.login : 'Гость'}</p>
                    {props.authorized ? <Link to='/' onClick={onLogoutHandler}><p className='sign'>Выйти</p></Link> : 
                    <Link to='/sign-in'><p className='sign'>Войти</p></Link>}
                </div>
            </div>
    </header>
);
}
export default Header