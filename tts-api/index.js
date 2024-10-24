const express = require('express');
const cors = require('cors');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 3389;
const BASE_PATH = process.env.BASE_PATH || '/api/tts'; // 기본 경로 설정

app.use(cors());
app.use(express.json());

app.post('/api/tts', async (req, res) => {
    // console.log('Received request at /api/tts');
    try {
        const { input } = req.body;
        // console.log('Received text:', input);
        
        const response = await fetch('https://api.openai.com/v1/audio/speech', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: 'tts-1',
                input: input,
                voice: 'nova',
                response_format: 'opus',
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('OpenAI API Error:', errorText);
            throw new Error(`OpenAI API error: ${response.status}`);
        }

        const audioBuffer = await response.arrayBuffer();
        // console.log('Received audio buffer size:', audioBuffer.byteLength);
        
        res.set('Content-Type', 'audio/opus');
        res.send(Buffer.from(audioBuffer));
        
    } catch (error) {
        // console.error('Error in /tts:', error);
        res.status(500).json({ error: error.message });
    }
});

app.listen(port, () => {
    console.log(`Local Edge Function server running on port ${port}`);
    console.log(`TTS endpoint available at ${BASE_PATH}`);
});