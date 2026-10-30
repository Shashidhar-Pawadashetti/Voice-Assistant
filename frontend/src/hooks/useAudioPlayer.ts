import { useCallback, useEffect, useRef, useState } from 'react';
import { fetchAuthenticatedAudioBlobUrl } from '../services/audio';

export function useAudioPlayer() {
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentAudioPath, setCurrentAudioPath] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    const audio = new Audio();
    audioRef.current = audio;

    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentAudioPath(null);
    };

    const handleError = () => {
      setIsPlaying(false);
      setIsLoading(false);
      setError('ಆಡಿಯೋ ಪ್ಲೇ ಮಾಡಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ (Audio playback failed)');
    };

    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('error', handleError);

    return () => {
      audio.pause();
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('error', handleError);
      audio.src = '';
    };
  }, []);

  const play = useCallback(async (audioPath: string) => {
    setError(null);
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying && currentAudioPath === audioPath) {
      audio.pause();
      setIsPlaying(false);
      return;
    }

    try {
      setIsLoading(true);
      const blobUrl = await fetchAuthenticatedAudioBlobUrl(audioPath);
      audio.src = blobUrl;
      await audio.play();
      setIsPlaying(true);
      setCurrentAudioPath(audioPath);
    } catch (err: any) {
      setError(err.message || 'ಧ್ವನಿ ಲೋಡ್ ಮಾಡಲು ವಿಫಲವಾಗಿದೆ');
      setIsPlaying(false);
    } finally {
      setIsLoading(false);
    }
  }, [isPlaying, currentAudioPath]);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setIsPlaying(false);
    setCurrentAudioPath(null);
  }, []);

  return {
    isPlaying,
    isLoading,
    currentAudioPath,
    error,
    play,
    stop,
  };
}
