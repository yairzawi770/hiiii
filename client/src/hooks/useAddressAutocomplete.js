import { useEffect, useMemo, useRef, useState } from 'react';
import { debounce } from '../functions/debounce';
import { searchIsraeliAddresses } from '../functions/addressService';

export function useAddressAutocomplete(value, setValue) {
  const [selected, setSelected] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [openField, setOpenField] = useState(false);

  const valueRef = useRef('');
  valueRef.current = value;

  const debouncedSearch = useMemo(
    () =>
      debounce(async (query) => {
        const results = await searchIsraeliAddresses(query);

        if (valueRef.current.trim() === query) {
          setSuggestions(results);
          setIsLoading(false);
        }
      }, 150),
    [],
  );

  useEffect(() => {
    const query = value.trim();

    if (query.length < 2) {
      setSuggestions([]);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    debouncedSearch(query);
  }, [value, debouncedSearch]);

  useEffect(() => {
    return () => debouncedSearch.cancel();
  }, [debouncedSearch]);

  const selectSuggestion = (suggestion) => {
    setValue(suggestion.label);
    setSelected(suggestion);
    setSuggestions([]);
    setOpenField(false);
  };

  return {
    selected,
    setSelected,
    suggestions,
    isLoading,
    openField,
    setOpenField,
    selectSuggestion,
  };
}