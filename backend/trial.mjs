import fetch from 'node-fetch';

const response = fetch('https://1288-102-90-64-162.ngrok-free.app/api/v1/token/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        email: "gofy6566@gmail.com",
        password: "testing123",
    }),
})
.then(response => {
    if (!response.ok) {
        throw new Error('Network response was not ok ' + response.statusText);
    }
    return response.json();
})
.then(data => {
    console.log('Success:', data);
})
.catch(error => {
    console.error('Error:', error);
});



console.log(response.body);