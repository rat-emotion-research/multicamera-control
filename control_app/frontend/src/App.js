import logo from './logo.svg';
import './App.scss';
import { Button, ButtonGroup } from "@chakra-ui/react"

import { SettingsIcon, ChevronDownIcon } from '@chakra-ui/icons'
import { IconButton } from "@chakra-ui/react"

import React, { Component } from 'react';
import { ChakraProvider } from "@chakra-ui/react"
import { Switch } from "@chakra-ui/react"

import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
} from "@chakra-ui/react"

import {
  Table,
  Thead,
  Tbody,
  Tfoot,
  Tr,
  Th,
  Td,
  TableCaption,
} from "@chakra-ui/react"

import { Select } from "@chakra-ui/react"

import {
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
} from "@chakra-ui/react"

class VideoSensorSettings extends Component {
  settingsFieldOrder = ['Name', 'default']
  constructor(props) {
    super(props)
    this.state = {
      open: false,
      options: {data: []}
    }
  }

  onOpen = () => {
    this.setState({open: true})
    this.getSettings()
  }
  onClose = () => this.setState({open: false})
  
  async updateSettings(name, value) {
    const response = await fetch(`http://${this.props.url}/settings/${name}`, {
      method: 'PUT',
      cache: 'no-cache',
      headers: {'Access-Control-Allow-Origin': `http://${this.props.url}`},
      body: value
    })
  }

  async getSettings() {
    console.log(`http://${this.props.url}/settings`)
    const response = await fetch(`http://${this.props.url}/settings`, {
      method: 'GET',
      cache: 'no-cache',
      headers: {'Access-Control-Allow-Origin': `http://${this.props.url}`}
    })
    let data = await response.json()
    console.log(data)
    this.setState({ options: data })
  }

  renderOption = (option) => {
    let control;
    let onChange = (value) => {
      this.updateSettings(option.name, value)
    }

    switch (option.dtype) {
      case 'menu':
        control = (<Select 
          name={option.name}
          defaultValue={option.value}
          onChange={(evt)=>onChange(evt.target.value)}>
          {option.options.map(
            item=><option value={item.value}>{item.display}</option>)}
        </Select>)
        break
      case 'int':
        control = (<NumberInput 
          defaultValue={option.value}
          step={option.step}
          min={option.min}
          max={option.max}
          name={option.name}
          onChange={(evt)=>onChange(evt)}>
          <NumberInputField />
          <NumberInputStepper>
            <NumberIncrementStepper />
            <NumberDecrementStepper />
          </NumberInputStepper>
        </NumberInput>)
        break
      case 'bool':
        control = <Switch 
          size='lg' 
          onChange={(evt)=>onChange(evt.target.checked)}
          name={option.name} 
          defaultChecked={option.value} />
        break
      default: 
        control = 'N/A'
    }

    return (<Tr>
      <Td>{option.name} (default: {option.default})</Td>
      <Td>{control}</Td>
    </Tr>)
  }

  renderOptions() {
    return (
      <Table variant="simple" className="options-table">
      <Thead>
        <Tr>
         <Th>Name</Th>
         <Th size="xl">Control</Th>
        </Tr>
      </Thead>
      <Tbody>
        {this.state.options.data.map(this.renderOption)}
      </Tbody>
      </Table>
    )
  }

  reset = () => {
    this.state.options.data.forEach((option)=>{
      console.log(option.name, option.value)
      this.updateSettings(option.name, option.value)
    })
    this.setState({})
  }

  render() {
    return (
      <div className="camera-settings">
        <IconButton
          onClick={this.onOpen}
          size="lg"
          colorScheme="teal"
          aria-label="Search database"
          icon={<SettingsIcon />}
        />,
        <Modal isOpen={this.state.open} size={'6xl'} 
          onClose={this.onClose}>
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>Sensor: {this.props.url}</ModalHeader>
            <ModalCloseButton />
            <ModalBody className='camera-settings-body'>
              <img key={this.props.url} src={`http://${this.props.url}/video_feed`}
                className='video-feed'></img>
              <div className="options">
                {this.renderOptions()}
              </div>
            </ModalBody>

            <ModalFooter>
              <Button colorScheme="blue" mr={3} onClick={this.onClose}>
                Close
            </Button>
              <Button variant="ghost" onClick={this.reset}>Reset</Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </div>
    );
  }
}


function VideoSensor(props) {
  return (
    <div className='video-sensor'>
      <h2>{props.url}</h2>
      <img key={props.url} src={`http://${props.url}/video_feed`}
        className='video-feed'></img>
      <VideoSensorSettings url={props.url}></VideoSensorSettings>
    </div>
  )
}

class App extends Component {
  constructor() {
    super()
    this.state = { sensors: [] }
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
    this.setState({ sensors: data })
  }

  startRecording() {
    this.state.sensors.forEach(address => {
      fetch(`http://${address}/start_recording`, {
        method: 'GET',
        mode: 'no-cors',
        cache: 'no-cache',
        credentials: 'same-origin',
      })
    })
  }

  stopRecording() {
    this.state.sensors.forEach(address => {
      fetch(`http://${address}/stop_recording`, {
        method: 'GET',
        mode: 'no-cors',
        cache: 'no-cache',
        credentials: 'same-origin',
      })
    })
  }

  render() {
    let sensorDisplay = this.state.sensors.map(
      sensor => <VideoSensor url={sensor}></VideoSensor>)

    return (
      <ChakraProvider>
        <div className="App">
          <div class="controlbar">
            <ButtonGroup size="md" colorScheme="teal">
              <Button onClick={this.startRecording.bind(this)}> Start</Button>
              <Button onClick={this.stopRecording.bind(this)}> Stop</Button>
              <Button onClick={this.stopRecording.bind(this)}> Download</Button>
            </ButtonGroup>

            <ButtonGroup size="md" colorScheme="teal">
              <Button onClick={this.startRecording.bind(this)}> Add Camera </Button>
            </ButtonGroup>
          </div>
          <div className="sensors-container">
            {sensorDisplay}
          </div>
        </div>
      </ChakraProvider>
    );
  }
}

export default App;
