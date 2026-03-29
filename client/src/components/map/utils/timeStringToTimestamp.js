export default function timeStringToTimestamp(timeString) {
    const hours = parseInt(timeString.slice(0, 2), 10);
    const minutes = parseInt(timeString.slice(3, 5), 10);

    const now = new Date();

    const date = new Date(
        now.getFullYear(),
        now.getMonth(),
        now.getDate(),
        hours,
        minutes
    );

    if (date < now) {
        date.setDate(date.getDate() + 1);
    }

    return Math.floor(date.getTime() / 1000);
}