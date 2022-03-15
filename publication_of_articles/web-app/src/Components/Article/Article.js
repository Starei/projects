import React from "react";
import { List } from "antd";
import { SmileOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';
import "./Article.scss";

const IconText = ({ type, text }) => (
  <span>
    <SmileOutlined
      type={type}
      style={{
        marginRight: 8
      }}
    />
    {text}
  </span>
);

const Articles = props => {
  return (
    <List
      itemLayout="vertical"
      size="large"
      pagination={{
        onChange: page => {
          console.log(page);
        },
        pageSize: 2
      }}
      dataSource={props.data}
      renderItem={item => (
        <List.Item
          key={item.title}
          actions={[
            <IconText type="star-o" text="156" />,
            <IconText type="like-o" text="156" />,
            <IconText type="message" text="2" />,
          ]}
          extra={
            <img
              width={272}
              alt="logo"
              src={item.image}
            />
          }
        >
          <List.Item.Meta
            avatar={<img src={item.avatar} alt="avatar" className="avatar"/>}
            title={<Link to={{
              pathname:`/list/${item.id}/`,
              id: item.id,
              list: props.type_list,
              login: props.login,
            }}> {item.title} </Link>}
            description={item.kind}
          />
          <p className="user">{item.login}</p>
          <p className="content">{item.description}</p>
        </List.Item>
      )}
    />
  );
};

export default Articles;