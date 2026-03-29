function AutocompleteField({
  label,
  value,
  onChange,
  placeholder,
  suggestions,
  isLoading,
  open,
  setOpen,
  onSelect,
}) {
  return (
    <label className="autocomplete-field">
      {label}
      <input
        type="text"
        value={value}
        onChange={onChange}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 120)}
        placeholder={placeholder}
      />

      {open && (isLoading || suggestions.length > 0) ? (
        <ul className="suggestions-list">
          {isLoading ? (
            <li className="suggestion-status">טוען הצעות...</li>
          ) : null}

          {!isLoading
            ? suggestions.map((suggestion) => (
                <li key={suggestion.id}>
                  <button
                    type="button"
                    className="suggestion-button"
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => onSelect(suggestion)}
                  >
                    {suggestion.label}
                  </button>
                </li>
              ))
            : null}
        </ul>
      ) : null}
    </label>
  );
}

export default AutocompleteField;