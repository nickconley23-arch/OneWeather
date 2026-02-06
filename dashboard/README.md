# OneWeather Dashboard - Standalone Version

**Status**: Safe development (no CI/CD triggers)
**Target**: Integration into 1news.co/weather
**Demo Location**: Ardmore, PA (40.0048, -75.2923)
**Style**: Apple/Tesla Dark Theme

## Structure:
- `index.html` - Main dashboard (Dark Sky/Apple style)
- `weather.js` - API integration and UI logic
- `styles.css` - Tailwind + custom dark theme
- `api/` - Local proxy to our FastAPI backend

## Safety Protocol:
1. This is standalone - won't touch 1news.co repo
2. When ready, will copy minimal files to 1news.co
3. CI/CD only triggered when we intentionally push

## Development Plan:
1. Build polished UI here
2. Test with our backend API
3. Show demo for approval
4. Plan safe integration