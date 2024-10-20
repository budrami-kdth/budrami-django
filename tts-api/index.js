// local-edge-server.js
const express = require('express');
const cors = require('cors');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

// local-edge-server.js
app.post('/tts', async (req, res) => {
    console.log('Received request at /tts'); // 요청 로그 추가
    try {
        const { input } = req.body;
        console.log('Received text:', input); // 받은 텍스트 로그 추가
        
        const response = await fetch('https://api.openai.com/v1/audio/speech', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: 'tts-1',
                input: input,
                voice: 'nova'
            })
        });
        console.log('response:', response)
        const audioBuffer = await response.arrayBuffer();
        res.set('Content-Type', 'audio/mpeg');
        res.send(Buffer.from(audioBuffer));
    } catch (error) {
        console.error('Error in /tts:', error.message);
        res.status(500).json({ error: error.message });
    }
});



app.listen(3000, () => {
  console.log('Local Edge Function server running on port 3000');
});