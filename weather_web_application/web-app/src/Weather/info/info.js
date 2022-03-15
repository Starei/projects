
const Info = ({city}) => (
    <div>
        {city ? <h1>{city}</h1> : <p>Наберите любой город который хотите</p>}
    </div>
)

export default Info;