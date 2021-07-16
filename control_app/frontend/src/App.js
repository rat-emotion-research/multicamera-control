import logo from './logo.svg';
import './App.scss';

import React, { Component } from 'react';

class App extends Component {
  constructor() {
    super()
    this.state = {sensors: []}
  }
  
  componentDidMount() {
    this.getSensors()
  }
  
  async getSensors() {
    const response = await fetch('/sensors', {
      method: 'GET',
      mode: 'no-cors',
      cache: 'no-cache',
      credentials: 'same-origin',
    })
    let data = await response.json()
    console.log('Sensors', data)
    this.setState({sensors: data})
  }

  render() {
    let sensorDisplay = this.state.sensors.map(
      sensor => <img key={sensor} src={`http://${sensor}/video_feed`}></img>)

    return (
      <div className="App">
        {sensorDisplay}
      </div>
    );
  }
}

export default App;
