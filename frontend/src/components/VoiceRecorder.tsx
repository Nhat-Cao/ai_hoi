import React, { useState, useRef } from 'react';import React, { useState, useRef } from 'react';

import { DEFAULT_BACKEND } from '@/service/api';import { DEFAULT_BACKEND } from '@/service/api';



interface VoiceRecorderProps {interface VoiceRecorderProps {

  onTranscription: (text: string) => void;  onTranscription: (text: string) => void;

}}



const VoiceRecorder: React.FC<VoiceRecorderProps> = ({ onTranscription }) => {const VoiceRecorder: React.FC<VoiceRecorderProps> = ({ onTranscription }) => {

  const [isRecording, setIsRecording] = useState(false);  const [isRecording, setIsRecording] = useState(false);

  const [isProcessing, setIsProcessing] = useState(false);  const [isProcessing, setIsProcessing] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  const audioChunksRef = useRef<Blob[]>([]);  const audioChunksRef = useRef<Blob[]>([]);



  const startRecording = async () => {  const startRecording = async () => {

    try {    try {

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      const mediaRecorder = new MediaRecorder(stream);      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorderRef.current = mediaRecorder;      mediaRecorderRef.current = mediaRecorder;

      audioChunksRef.current = [];      audioChunksRef.current = [];



      mediaRecorder.ondataavailable = (event) => {      mediaRecorder.ondataavailable = (event) => {

        if (event.data.size > 0) {        if (event.data.size > 0) {

          audioChunksRef.current.push(event.data);          audioChunksRef.current.push(event.data);

        }        }

      };      };



      mediaRecorder.onstop = async () => {      mediaRecorder.onstop = async () => {

        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });

        await sendAudioToBackend(audioBlob);        await sendAudioToBackend(audioBlob);

                

        // Stop all tracks        // Stop all tracks

        stream.getTracks().forEach(track => track.stop());        stream.getTracks().forEach(track => track.stop());

      };      };



      mediaRecorder.start();      mediaRecorder.start();

      setIsRecording(true);      setIsRecording(true);

    } catch (error) {    } catch (error) {

      console.error('Error accessing microphone:', error);      console.error('Error accessing microphone:', error);

      alert('Could not access microphone. Please check permissions.');      alert('Could not access microphone. Please check permissions.');

    }    }

  };  };



  const stopRecording = () => {  const stopRecording = () => {

    if (mediaRecorderRef.current && isRecording) {    if (mediaRecorderRef.current && isRecording) {

      mediaRecorderRef.current.stop();      mediaRecorderRef.current.stop();

      setIsRecording(false);      setIsRecording(false);

    }    }

  };  };



  const sendAudioToBackend = async (audioBlob: Blob) => {  const sendAudioToBackend = async (audioBlob: Blob) => {

    setIsProcessing(true);    setIsProcessing(true);

    try {    try {

      const formData = new FormData();      const formData = new FormData();

      formData.append('audio', audioBlob, 'recording.wav');      formData.append('audio', audioBlob, 'recording.wav');



      const response = await fetch(`${DEFAULT_BACKEND}/speech-to-text`, {      const response = await fetch(`${DEFAULT_BACKEND}/speech-to-text`, {

        method: 'POST',        method: 'POST',

        body: formData,        body: formData,

      });      });



      const data = await response.json();      const data = await response.json();

      if (data.text) {      if (data.text) {

        onTranscription(data.text);        onTranscription(data.text);

      } else if (data.error) {      } else if (data.error) {

        console.error('Transcription error:', data.error);        console.error('Transcription error:', data.error);

        alert('Failed to transcribe audio. Please try again.');        alert('Failed to transcribe audio. Please try again.');

      }      }

    } catch (error) {    } catch (error) {

      console.error('Error sending audio:', error);      console.error('Error sending audio:', error);

      alert('Failed to process audio. Please try again.');      alert('Failed to process audio. Please try again.');

    } finally {    } finally {

      setIsProcessing(false);      setIsProcessing(false);

    }    }

  };  };



  return (  return (

    <button    <button

      type="button"      type="button"

      onClick={isRecording ? stopRecording : startRecording}      onClick={isRecording ? stopRecording : startRecording}

      disabled={isProcessing}      disabled={isProcessing}

      className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${      className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${

        isRecording        isRecording

          ? 'bg-red-500 hover:bg-red-600 animate-pulse'          ? 'bg-red-500 hover:bg-red-600 animate-pulse'

          : isProcessing          : isProcessing

          ? 'bg-gray-600 cursor-not-allowed'          ? 'bg-gray-600 cursor-not-allowed'

          : 'bg-orange-400 hover:bg-orange-300'          : 'bg-orange-400 hover:bg-orange-300'

      } text-white focus:outline-none`}      } text-white focus:outline-none`}

      title={isRecording ? 'Stop recording' : 'Start voice input'}      title={isRecording ? 'Stop recording' : 'Start voice input'}

    >    >

      {isProcessing ? (      {isProcessing ? (

        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">

          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />

          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />

        </svg>        </svg>

      ) : isRecording ? (      ) : isRecording ? (

        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">

          <rect x="6" y="6" width="8" height="8" rx="1" />          <rect x="6" y="6" width="8" height="8" rx="1" />

        </svg>        </svg>

      ) : (      ) : (

        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">

          <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />          <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />

        </svg>        </svg>

      )}      )}

    </button>    </button>

  );  );

};};



export default VoiceRecorder;export default VoiceRecorder;
