import React from "react";
import axios from "axios";
import Articles from "./Article";
import './List.scss';


class ArticleList extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      articles: [],
      list: this.props.list,
      login: this.props.login,
    };
  }

  fetchArticles = () => {
    let type_list = this.state.list;
    let type = type_list
    if (type_list === "all" || type_list === "my")
      type_list = "list"
    let Articles = []
    axios.get(`http://localhost:8000/api/${type_list}/`).then(res => {
      Articles = res.data;
      if (type === "my") {
        this.setState({
          articles: Articles.filter(article => {return article.login === this.state.login}).map(
            article => {return article})
        })
      }
      else {
        if (this.state.list === "checklist" && this.state.login.slice(0, 5) !== 'admin')
        {
          this.setState({
            articles: Articles.filter(article => {return article.login === this.state.login}).map(
              article => {return article})
          })
        }
        else {
          this.setState({
            articles: Articles
          });
        }
      } 
    })
  }

  componentDidMount() {
    this.fetchArticles();
  }

  

  render() {
    return (
      <div className="List">
          <Articles login={this.state.login} data={this.state.articles} type_list={this.state.list}/> <br />
      </div>
    );
  }
}

export default ArticleList;