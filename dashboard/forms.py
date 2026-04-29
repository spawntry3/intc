from django import forms


class ImportInstagramPostsForm(forms.Form):
    csv_file = forms.FileField(label="CSV файл (UTF-8)", required=True)
    delimiter = forms.ChoiceField(
        label="Разделитель",
        choices=[("auto", "Авто"), (";", ";"), (",", ",")],
        initial="auto",
        required=False,
    )
    mode = forms.ChoiceField(
        label="Режим загрузки",
        choices=[
            ("append", "Добавить/обновить по `post_id`"),
            ("replace_source", "Заменить все записи Instagram-постов"),
        ],
        initial="append",
    )


class ImportReviewsForm(forms.Form):
    csv_file = forms.FileField(label="CSV файл (UTF-8)", required=True)
    delimiter = forms.ChoiceField(
        label="Разделитель",
        choices=[("auto", "Авто"), (";", ";"), (",", ",")],
        initial="auto",
        required=False,
    )
    mode = forms.ChoiceField(
        label="Режим загрузки",
        choices=[
            ("append", "Добавить (без удаления старых)"),
            ("replace_source", "Заменить все отзывы указанного источника"),
        ],
        initial="append",
    )

