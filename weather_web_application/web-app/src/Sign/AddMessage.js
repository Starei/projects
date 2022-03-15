import React, {Component} from "react";
import { Button, Form, FormGroup, Label, Input} from "reactstrap";
import axios from "axios";
import { Redirect, Link } from "react-router-dom";


export default class AddMessage extends Component {
    userData;
    constructor(props) {
      super(props);
      this.state = {
        messageData: {
          type: "",
          level: "",
          message: "",
        },
        msg: "",
        radioValue: "",
      };
    }
  
    onChangehandler = (e, key) => {
      const { messageData } = this.state;
      messageData[e.target.name] = e.target.value;
      this.setState({ messageData });
    };
    onSubmitHandler = (e) => {
      e.preventDefault();
      console.log("send");
      axios
        .post("http://localhost:8000/api/add-message", this.state.messageData)
        .then((response) => {
            console.log("Send");
            localStorage.setItem("DataSend", true);
            this.setState({
              msg: response.data.message,
              messageData: {
                type: "",
                level: "",
                message: "",
              },
            });
            setTimeout(() => {
              this.setState({ msg: ""});
            }, 2000);
  /*
          if (response.data.status === "failed") {
            this.setState({ msg: response.data.message });
            setTimeout(() => {
              this.setState({ msg: "" });
            }, 2000);
          }*/
        });
    };
    render() {

      const login = localStorage.getItem("DataSend");
    
      if (login) {
        return <Redirect to="/"/>;
      }

      return (
        <div>
          <Form className="containers shadow">
            <FormGroup>
              <Label for="type">Type</Label>
              <Input
                type="type"
                name="type"
                placeholder="Enter type"
                value={this.state.messageData.type}
                onChange={this.onChangehandler}
              />
            </FormGroup>
            <FormGroup>
              <Label for="level">Level</Label>
              <Input
                type="level"
                name="level"
                placeholder="Enter level"
                value={this.state.messageData.level}
                onChange={this.onChangehandler}
              />
            </FormGroup>
            <FormGroup>
              <Label for="message">Message</Label>
              <Input
                type="message"
                name="message"
                placeholder="Enter message"
                value={this.state.messageData.message}
                onChange={this.onChangehandler}
              />
            </FormGroup>
            <p className="text-white">{this.state.msg}</p>
            <Button
              className="text-center mb-4"
              color="success"
              onClick={this.onSubmitHandler}
            >
              Send
            </Button>
            <span className="p-3">
              <Link to="/" className="text-white ml-5">Назад</Link>
            </span> 
          </Form>
        </div>
      );
    }
  }
