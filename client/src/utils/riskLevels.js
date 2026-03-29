export function getRiskLevel(riskPercent) {
  if (riskPercent <= 25) return 'low';
  if (riskPercent <= 60) return 'medium';
  if (riskPercent <= 85) return 'high';
  return 'extreme';
}

export function getRiskLevelTitle(level) {
  switch (level) {
    case 'low':
      return 'סיכון נמוך';
    case 'medium':
      return 'סיכון בינוני';
    case 'high':
      return 'סיכון גבוה';
    case 'extreme':
      return 'סיכון קיצוני';
    default:
      return 'סיכון';
  }
}

export function getRiskShortMessage(level) {
  switch (level) {
    case 'low':
      return 'סע בזהירות';
    case 'medium':
      return 'סע בסמיכות למרחב מוגן';
    case 'high':
      return 'אזהרת מסע';
    case 'extreme':
      return 'אזהרת מסע חמורה';
    default:
      return '';
  }
}

export function getRiskLongMessage(level) {
  switch (level) {
    case 'low':
      return 'הדרך נראית בטוחה יחסית, אבל עדיין חשוב להישאר ערני.';
    case 'medium':
      return 'מומלץ לבחור מסלול מוכר ולהימנע מאזורים בעייתיים ככל האפשר.';
    case 'high':
      return 'שקול מסלול חלופי או דחייה של הנסיעה במידת האפשר.';
    case 'extreme':
      return 'מומלץ להימנע מהנסיעה. אם חייבים לצאת, היערכות מוקדמת היא חובה.';
    default:
      return '';
  }
}