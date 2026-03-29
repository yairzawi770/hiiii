import { useState } from 'react';
import { validateTripForm } from '../utils/validateTripForm';
import { useMapRoute } from '../components/map/hooks/useMapRoute';
import { useRouteStore } from '../components/zustand/store';

export function useTripSubmit(onPlanned) {
  const [submitMessage, setSubmitMessage] = useState('');
  const [submitError, setSubmitError] = useState('');

  const {
    origin,
    destination,
    departureTime,
    isSubmitting,
    setIsSubmitting,
  } = useRouteStore();

  const { loadRoute } = useMapRoute();

  const handleSubmit = async ({
    selectedOrigin,
    selectedDestination,
    event,
  }) => {
    event.preventDefault();
    setSubmitMessage('');
    setSubmitError('');

    const error = validateTripForm({
      origin,
      destination,
      departureTime,
      selectedOrigin,
      selectedDestination,
    });

    if (error) {
      setSubmitError(error);
      return;
    }

    setIsSubmitting(true);

    try {
      await loadRoute();
      setSubmitMessage('הנסיעה תוכננה בהצלחה.');

      if (typeof onPlanned === 'function') {
        onPlanned();
      }
    } catch (err) {
      setSubmitError(err.message || 'תכנון נכשל, נסה שוב.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    submitMessage,
    submitError,
    isSubmitting,
    handleSubmit,
  };
}