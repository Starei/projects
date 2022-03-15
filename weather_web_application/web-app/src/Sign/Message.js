import React, { Component } from "react";
import { Table } from "reactstrap";
import axios from "axios";


export default class Users extends Component {
    constructor(props){
        super(props);
        this.state = {
            reports: [],
        }
    }

    componentDidMount() {
        this.getReports();
      }      
      getReports() {
    axios.get("http://localhost:8000/api/reports").then((response) => {
        if (response.status === 200) {
        this.setState({
            reports: response.data.data ? response.data.data : [],
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

  render() {
    localStorage.clear();
    const { noDataFound, reports} = this.state;
      let reportsDetails = [];
      if (reports.length) {
        reportsDetails = reports.map((report) => {
          return (
            <tr key={report.id}>
              <td>{report.id}</td>
              <td>{report.type}</td>
              <td>{report.level}</td>
              <td>{report.message}</td>
            </tr>
          );
        });
      }
   
    return (
        <div className='Table'>
      <div className="container mt-4 bg-white">
           <h3 className="font-weight-bold text-center text-danger">Сообщения</h3>
        <Table>
          <thead>
            <tr>
              <th>#</th>
              <th>Type</th>
              <th>Level</th>
              <th>Message</th>
            </tr>
          </thead>
          {reports.length === 0 ? (
            <tbody>
              <h3>{noDataFound}</h3>
            </tbody>
          ) : (
            <tbody>{reportsDetails}</tbody>
          )}
        </Table>
      </div>
      </div>
    );
  }
}