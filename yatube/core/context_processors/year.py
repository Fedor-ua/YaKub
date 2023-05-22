from datetime import datetime

now = datetime.today()
now_year = now.year


def year(request):
    """Добавляет переменную с текущим годом."""
    return {'year': now.year}
