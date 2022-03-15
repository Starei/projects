import React from 'react';
import { Link } from 'react-router-dom';
import './FAQ.scss';

const FAQ = (props) => {
    const type = props.location.id
    

    return (
        <div className="FAQ">
            <div className="FAQ-wrapper">
                <h1 className="title">FAQ</h1>
                { type === 'FAQ' ?
                    <div className="text">
                        The visitor can only view articles. 
                        To be able to create articles yourself and work with them, 
                        you need to register and log into your account. 
                        After the above steps are completed, 
                        the user will also be able to view his own articles. 
                        Editing of articles is carried out only by the author himself.
                    </div>
                    :
                    <div className="text">
                        Чтобы осуществить экспорт или импорт нажмите кнопки в шапке страницы
                        "Выгрузить" и "Загрузить" соответственно. Учтите, что будут выгружены
                        только те статьи, которые прошли модерацию (проверку). Для того
                        чтобы статьи загрузить нужно сначала их выгрузить, обратно - так же. 
                    </div>
                }
                <Link to='/' className='react-link'>
                    <p>OK</p>
                </Link>
            </div>
        </div>
    )
}

export default FAQ;