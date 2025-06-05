import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

def fetch_forex_factory_news():
    url = 'https://www.forexfactory.com/calendar.php'
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    news_items = []

    # Forex Factory's calendar uses specific IDs and classes; these may change over time
    # Adjust the selectors accordingly if the structure changes
    rows = soup.find_all('tr', class_='calendar_row')

    for row in rows:
        try:
            time_cell = row.find('td', class_='time')
            currency_cell = row.find('td', class_='currency')
            impact_cell = row.find('td', class_='impact')
            event_cell = row.find('td', class_='event')
            actual_cell = row.find('td', class_='actual')
            forecast_cell = row.find('td', class_='forecast')

            if not all([time_cell, currency_cell, impact_cell, event_cell]):
                continue

            time_str = time_cell.get_text(strip=True)
            currency = currency_cell.get_text(strip=True)
            impact = impact_cell.find('span')['title'] if impact_cell.find('span') else ''
            event = event_cell.get_text(strip=True)
            actual = actual_cell.get_text(strip=True)
            forecast = forecast_cell.get_text(strip=True)

            # Parse time; Forex Factory times are in ET by default
            # Adjust to your local timezone if necessary
            event_time = datetime.strptime(time_str, '%I:%M%p').replace(
                year=datetime.now().year,
                month=datetime.now().month,
                day=datetime.now().day
            )
            event_time = pytz.timezone('US/Eastern').localize(event_time)

            news_items.append({
                'time': event_time,
                'currency': currency,
                'impact': impact,
                'event': event,
                'actual': actual,
                'forecast': forecast
            })
        except Exception as e:
            # Handle any parsing errors
            continue

    return news_items

def analyze_sentiment(news_items):
    sentiment_scores = []

    for item in news_items:
        # Simple sentiment analysis based on actual vs forecast
        # This is a placeholder; for more accurate analysis, integrate with a sentiment analysis model
        try:
            actual = float(item['actual'].replace(',', ''))
            forecast = float(item['forecast'].replace(',', ''))
            if actual > forecast:
                sentiment = 1  # Positive sentiment
            elif actual < forecast:
                sentiment = -1  # Negative sentiment
            else:
                sentiment = 0  # Neutral sentiment
        except:
            sentiment = 0  # Unable to determine sentiment

        sentiment_scores.append({
            'time': item['time'],
            'currency': item['currency'],
            'event': item['event'],
            'sentiment': sentiment
        })

    return sentiment_scores
