import React, { Component } from "react";
import { Table, Button } from "reactstrap";
import axios from "axios";

export default class Users extends Component {
    constructor(props){
        super(props);
        this.state = {
            users: [],
        }
    }

    componentDidMount() {
        this.getUsers();
      }      
      getUsers() {
    axios.get("http://localhost:8000/api/users").then((response) => {
        if (response.status === 200) {
        this.setState({
            users: response.data.data ? response.data.data : [],
        });
        }
        if (
        response.data.status === "failed" &&
        response.data.success === false
        ) {
        this.setState({
            noDataFound: response.data.message,
        });
        }
    });
    }
    
    deletUser = (id) => {
      this.setState({
        isLoading: true,
      });
      axios
        .delete("http://localhost:8000/api/users/" + id)
        .then((response) => {
          this.setState({
            isLoading: false,
          });
          this.getUsers();
        })
        .catch((error) => {
          this.setState({
            isLoading: false,
          });
        });
    };

  render() {
    localStorage.clear();
    const { noDataFound, users} = this.state;
      let usersDetails = [];
      if (users.length) {
        usersDetails = users.map((user) => {
          return (
            <tr key={user.id}>
              <td>{user.id}</td>
              <td>{user.first_name}</td>
              <td>{user.last_name}</td>
              <td>{user.full_name}</td>
              <td>{user.email}</td>
              <td>{user.phone}</td>
              <td>
                <Button
                  color="danger"
                  size="sm"
                  onClick={() => this.deletUser(user.id)}
                >
                  Delete
                </Button>
              </td>
            </tr>
          );
        });
      }
   
    return (
        <div className='Table'>
      <div className="container mt-4 bg-white">
           <h3 className="font-weight-bold text-center text-danger">Пользователи</h3>
        <Table>
          <thead>
            <tr>
              <th>#</th>
              <th>First Name</th>
              <th>Last Name</th>
              <th>Full Name</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Action</th>
            </tr>
          </thead>
          {users.length === 0 ? (
            <tbody>
              <h3>{noDataFound}</h3>
            </tbody>
          ) : (
            <tbody>{usersDetails}</tbody>
          )}
        </Table>
      </div>
      </div>
    );
  }
}