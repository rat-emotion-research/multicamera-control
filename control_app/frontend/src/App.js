import logo from './logo.svg';
import './App.css';

const response = fetch('/sensors', {
  method: 'GET',
  mode: 'no-cors',
  cache: 'no-cache',
  credentials: 'same-origin',
  // body: JSON.stringify(data)
})
  .then(response => response.json())
  .then(data => console.log(data))

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>
          Edit <code>src/App.js</code> and save to reload.
        </p>
        <a
          className="App-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
          Learn React
        </a>
      </header>
    </div>
  );
}

export default App;
