import React, { useState } from 'react';
import axios from 'axios';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleLogin = async () => {
    try {
      const response = await axios.post('http://localhost:5000/login', {
        username,
        password,
      });
      localStorage.setItem('token', response.data.access_token);
      setIsLoggedIn(true);
    } catch (error) {
      setError(error.response.data.msg);
    }
  };

  const handleProtectedResource = async () => {
    try {
      const response = await axios.get('http://localhost:5000/protected', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });
      console.log(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div>
      {isLoggedIn ? (
        <div>
          <button onClick={handleProtectedResource}>
            Get Protected Resource
          </button>
        </div>
      ) : (
        <div>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button onClick={handleLogin}>Login</button>
          {error && <p>{error}</p>}
        </div>
      )}
    </div>
  );
};

export default Login;
