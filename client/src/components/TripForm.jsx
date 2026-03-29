import AutocompleteField from './AutocompleteField';
import { useAddressAutocomplete } from '../hooks/useAddressAutocomplete';
import { useTripSubmit } from '../hooks/useTripSubmit';
import { useRouteStore } from './zustand/store';

function TripForm({ onPlanned } = {}) {
  const {
    origin,
    destination,
    departureTime,
    setOrigin,
    setDestination,
    setDepartureTime,
  } = useRouteStore();

  const originAuto = useAddressAutocomplete(origin, setOrigin);
  const destinationAuto = useAddressAutocomplete(destination, setDestination);

  const {
    submitMessage,
    submitError,
    isSubmitting,
    handleSubmit,
  } = useTripSubmit(onPlanned);

  return (
    <section className="trip-form-card">
      <h1>תכנון נסיעה</h1>

      <form
        className="trip-form"
        onSubmit={(event) =>
          handleSubmit({
            event,
            selectedOrigin: originAuto.selected,
            selectedDestination: destinationAuto.selected,
          })
        }
      >
        <AutocompleteField
          label="מוצא"
          value={origin}
          onChange={(e) => {
            setOrigin(e.target.value);
            originAuto.setSelected(null);
          }}
          placeholder="לדוגמה: תל אביב"
          suggestions={originAuto.suggestions}
          isLoading={originAuto.isLoading}
          open={originAuto.openField}
          setOpen={originAuto.setOpenField}
          onSelect={originAuto.selectSuggestion}
        />

        <AutocompleteField
          label="יעד"
          value={destination}
          onChange={(e) => {
            setDestination(e.target.value);
            destinationAuto.setSelected(null);
          }}
          placeholder="לדוגמה: ירושלים"
          suggestions={destinationAuto.suggestions}
          isLoading={destinationAuto.isLoading}
          open={destinationAuto.openField}
          setOpen={destinationAuto.setOpenField}
          onSelect={destinationAuto.selectSuggestion}
        />

        <label>
          שעת יציאה
          <input
            type="time"
            value={departureTime}
            onChange={(e) => setDepartureTime(e.target.value)}
          />
        </label>

        <button type="submit" className="submit-button" disabled={isSubmitting}>
          {isSubmitting ? 'בודק...' : 'תכנן נסיעה'}
        </button>

        {submitMessage ? (
          <p className="submit-message success">{submitMessage}</p>
        ) : null}

        {submitError ? (
          <p className="submit-message error">{submitError}</p>
        ) : null}
      </form>
    </section>
  );
}

export default TripForm;