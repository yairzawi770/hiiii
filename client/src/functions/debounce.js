export function debounce(callback, wait = 300) {
  let timeoutId

  const debouncedFn = (...args) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => {
      callback(...args)
    }, wait)
  }

  debouncedFn.cancel = () => {
    clearTimeout(timeoutId)
  }

  return debouncedFn
}
