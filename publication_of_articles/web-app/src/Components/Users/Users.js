import React, { Component } from "react";
import { Table, Button } from "reactstrap";
import axios from "axios";

export default class Users extends Component {
    constructor(props){
        super(props);
        this.state = {
            users: [],
            usersban: [],
        }
    }

    componentDidMount() {
        this.getUsers();
        this.getUsersBan();
        this.checkUserBan();
      }      
    getUsers() {
    axios.get("http://localhost:8000/api/users/").then((response) => {
        if (response.status === 200) {
        console.log("users: ", response.data);
        this.setState({
            users: response.data ? response.data : [],
        });
        }
      });
      }

    getUsersBan() {
      axios.get("http://localhost:8000/api/userban/")
      .then((response) => {
        if (response.status === 200) {
          this.setState({
              usersban: response.data ? response.data : [],
          });
        }
      })
      .catch((error) => {
        console.log(error);
      })
    }

    banUser = (Login, DateValue) => {
      let dateValue = new Date(DateValue);
      let dateNow = new Date()
      if (dateValue.toString() === "Invalid Date")
      {
        alert("Выберите до какой даты");
      }
      else if (dateValue < dateNow)
      {
        alert("Дата > Сегодня");
      }
      else
      {
        let Date = dateValue.getFullYear().toString() + "-" +
        dateValue.getMonth() + "-" + dateValue.getDate().toString();
        axios.post(`http://localhost:8000/api/userban/`, {
          login: Login,
          date: Date,
        })
        .then((response) => {
          if (response.status === 201) {
            alert("Пользователь забанен");
            this.getUsersBan();
          }
        })
      }
    }

    checkUserBan() {
      let dateValue = {};
      let dateNow = new Date();
      let dateBan, year, month, day;
      this.state.usersban.map((user) => dateValue[user.id] = user.date.split('-'));
      for (let key in dateValue) {
        year = Number(dateValue[key][0])
        month = Number(dateValue[key][1])
        day = Number(dateValue[key][2])
        dateBan = new Date(year, month, day)
        if (dateNow > dateBan) {
          this.razbanUser(key)
        }
      }
    }

    razbanUser = (Login) => {
      let id = 0;
      let usersban = this.state.usersban;
      usersban.map((user) => {
        if (user.login === Login)
        {
          id = user.id;
        }
        return user;
      })
      axios
        .delete(`http://localhost:8000/api/userban/${id}/`)
        .then((response) => {
          alert("Пользователь разбанен");
          this.getUsersBan();
        })
    }
    
    deletUser = (id) => {
      axios
        .delete(`http://localhost:8000/api/users/${id}/`)
        .then((response) => {
          this.getUsers();
          this.razbanUser(id);
          this.getUsersBan();
        })
        .catch((error) => {
          console.log(error);
        });
    }

  render() {

    const { noDataFound, users} = this.state;
      let usersDetails = [];
      let dict = {};
      let usersBan = this.state.usersban.map((userban) => userban.login);
      this.state.usersban.map((userban) => dict[userban.login] = userban.date);
      let inc = 1;
      if (users.length) {
        usersDetails = users.filter(user => {return user.login.slice(0, 5) !== "admin"}).map((user) => {
          return (
              <tr key={user.id}>
              <td>{inc++}</td>
              <td>{user.login}</td>
              <td>
                  {usersBan.includes(user.login) ?
                    <Button
                      color="primary"
                      size="sm"
                      onClick={() => this.razbanUser(user.login)}
                    >
                      Разбан  
                    </Button>
                      :
                    <Button
                      color="warning"
                      size="sm"
                      onClick={() => this.banUser(user.login, document.getElementById(user.id).value)}
                    >
                      Бан  
                    </Button>
                  }
              </td>
              <td>
                  { usersBan.includes(user.login) ?
                    <span>
                     Бан до {dict[user.login]}
                    </span>
                    :
                    <span> 
                      <input id={user.id} type="date"/>             
                    </span>
                  }
              </td>
              <td>
                <Button
                  color="danger"
                  size="sm"
                  onClick={() => this.deletUser(user.id)}
                >
                  Удалить
                </Button>
              </td>
            </tr>
          );
        });
      }
   
    return (
      <div className="List">
        <div className='Table'>
          <div className="container mt-4 bg-white">
            <h3 className="font-weight-bold text-center text-danger">Пользователи</h3>
          <Table>
            <thead>
              <tr>
                <th>#</th>
                <th>Login</th>
                <th>Blocking</th>
                <th>Date</th>
                <th>Deleting</th>
              </tr>
            </thead>
            {users.length === 0 ? (
              <tbody>
                {noDataFound}
              </tbody>
            ) : (
              <tbody>{usersDetails}</tbody>
            )}
          </Table>
          </div>
        </div>
      </div>
    );
  }
}