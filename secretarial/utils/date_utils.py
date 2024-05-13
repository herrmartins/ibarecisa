from datetime import datetime


def date_to_words(date_str):
    try:
        # Parse the input date string into a datetime object
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")

        # Define lists for months and days
        months = [
            "janeiro",
            "fevereiro",
            "março",
            "abril",
            "maio",
            "junho",
            "julho",
            "agosto",
            "setembro",
            "outubro",
            "novembro",
            "dezembro",
        ]
        days = [
            "segunda-feira",
            "terça-feira",
            "quarta-feira",
            "quinta-feira",
            "sexta-feira",
            "sábado",
            "domingo",
        ]

        # Extract year, month, and day from the date object
        year = date_obj.year
        month = date_obj.month
        day = date_obj.day
        day_of_week = date_obj.weekday()  # 0 for Monday, 1 for Tuesday, etc.

        # Convert the date components to words
        month_word = months[month - 1]
        day_word = days[day_of_week]

        # Create the final formatted string
        # Tirei a formatação do dia para que possa ser um só digito
        # Se der pau, volte.
        date_in_words = f"{day} de {month_word} de {year:04d}, "

        return date_in_words
    except ValueError:
        return "Invalid date format. Please use YYYY-MM-DD."
