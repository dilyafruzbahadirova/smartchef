from django.conf import settings
from django.shortcuts import render
from dotenv import dotenv_values


def index(request):
    language = "kk"
    products = ""
    minutes = "30"
    vegetarian = False
    recipe = ""
    error = ""

    if request.method == "GET":
        language = request.GET.get("language", "kk")
        if language not in ("kk", "ru"):
            language = "kk"

        return render(
            request,
            "recipes/index.html",
            {
                "language": language,
                "products": products,
                "minutes": minutes,
                "vegetarian": vegetarian,
                "recipe": recipe,
                "error": error,
            },
        )

    language = request.POST.get("language", "kk")
    if language not in ("kk", "ru"):
        language = "kk"

    products = request.POST.get("products", "")
    minutes = request.POST.get("minutes", "30")
    vegetarian = request.POST.get("vegetarian") == "1"
    action = request.POST.get("action", "")

    if minutes not in ("15", "30", "60"):
        minutes = "30"

    if action == "language":
        return render(
            request,
            "recipes/index.html",
            {
                "language": language,
                "products": products,
                "minutes": minutes,
                "vegetarian": vegetarian,
                "recipe": "",
                "error": "",
            },
        )

    if action != "generate":
        return render(
            request,
            "recipes/index.html",
            {
                "language": language,
                "products": products,
                "minutes": minutes,
                "vegetarian": vegetarian,
                "recipe": "",
                "error": "",
            },
        )

    products_clean = products.strip()

    if len(products_clean) < 3:
        if language == "ru":
            error = "Введите продукты длиной не менее 3 символов."
        else:
            error = "Кемінде 3 таңбадан тұратын өнімдерді енгізіңіз."

        return render(
            request,
            "recipes/index.html",
            {
                "language": language,
                "products": products,
                "minutes": minutes,
                "vegetarian": vegetarian,
                "recipe": "",
                "error": error,
            },
        )

    if len(products_clean) > 500:
        if language == "ru":
            error = "Список продуктов не должен превышать 500 символов."
        else:
            error = "Өнімдер тізімі 500 таңбадан аспауы керек."

        return render(
            request,
            "recipes/index.html",
            {
                "language": language,
                "products": products,
                "minutes": minutes,
                "vegetarian": vegetarian,
                "recipe": "",
                "error": error,
            },
        )

    if minutes not in ("15", "30", "60"):
        if language == "ru":
            error = "Выберите время приготовления: 15, 30 или 60 минут."
        else:
            error = "Дайындау уақытын таңдаңыз: 15, 30 немесе 60 минут."

        return render(
            request,
            "recipes/index.html",
            {
                "language": language,
                "products": products,
                "minutes": minutes,
                "vegetarian": vegetarian,
                "recipe": "",
                "error": error,
            },
        )

    config = dotenv_values(settings.BASE_DIR / ".env")
    api_key = (config.get("GEMINI_API_KEY") or "").strip()
    model = (config.get("GEMINI_MODEL") or "").strip() or "gemini-3.8-flash"

    if not api_key or api_key == "PASTE_YOUR_KEY_HERE":
        if language == "ru":
            error = "Введите ключ Gemini в файл .env рядом с manage.py."
        else:
            error = "Gemini кілтін manage.py жанындағы .env файлына енгізіңіз."

        return render(
            request,
            "recipes/index.html",
            {
                "language": language,
                "products": products,
                "minutes": minutes,
                "vegetarian": vegetarian,
                "recipe": "",
                "error": error,
            },
        )

    if language == "ru":
        language_name = "русском языке"
        vegetarian_condition = (
            "Рецепт обязательно должен быть вегетарианским. "
            "Не используй мясо, птицу, рыбу и морепродукты."
            if vegetarian
            else "Вегетарианское ограничение не установлено."
        )

        prompt = f"""
Ты — помощник по приготовлению еды SmartChef.

Составь ровно один рецепт на {minutes} минут приготовления.

Доступные продукты пользователя:
{products_clean}

Язык ответа: {language_name}.

Условие:
{vegetarian_condition}

Используй доступные продукты разумно. Можно добавлять обычные базовые продукты и специи, если они необходимы для полноценного рецепта.

Ответ должен содержать только один рецепт и обязательно иметь:
1. Название блюда.
2. Время приготовления.
3. Ингредиенты с количеством.
4. Нумерованные пошаговые инструкции приготовления.
5. Один полезный совет.

Не предлагай несколько вариантов рецепта.
Не добавляй вступление или заключение вне структуры рецепта.
""".strip()
    else:
        language_name = "қазақ тілінде"
        vegetarian_condition = (
            "Рецепт міндетті түрде вегетариандық болуы керек. "
            "Ет, құс еті, балық және теңіз өнімдерін қолданба."
            if vegetarian
            else "Вегетариандық шектеу қойылмаған."
        )

        prompt = f"""
Сен — SmartChef тағам дайындау көмекшісісің.

{minutes} минутта дайын болатын дәл бір рецепт құрастыр.

Пайдаланушыдағы өнімдер:
{products_clean}

Жауап тілі: {language_name}.

Шарт:
{vegetarian_condition}

Қолжетімді өнімдерді орынды пайдалан. Толық рецепт дайындау үшін қажет болса, қарапайым негізгі өнімдер мен дәмдеуіштерді қосуға болады.

Жауапта міндетті түрде мыналар болсын:
1. Тағамның атауы.
2. Дайындау уақыты.
3. Мөлшері көрсетілген ингредиенттер.
4. Нөмірленген дайындау қадамдары.
5. Бір пайдалы кеңес.

Бірнеше рецепт ұсынба.
Құрылымнан тыс кіріспе немесе қорытынды қоспа.
""".strip()

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        interaction = client.interactions.create(model=model, input=prompt)
        recipe = interaction.output_text

        if not recipe or not recipe.strip():
            if language == "ru":
                error = "Не удалось получить рецепт. Попробуйте ещё раз."
            else:
                error = "Рецептті алу мүмкін болмады. Қайтадан көріңіз."
            recipe = ""

    except Exception:
        recipe = ""
        if language == "ru":
            error = "Не удалось создать рецепт. Проверьте настройки API и попробуйте ещё раз."
        else:
            error = "Рецепт жасау мүмкін болмады. API баптауларын тексеріп, қайтадан көріңіз."

    return render(
        request,
        "recipes/index.html",
        {
            "language": language,
            "products": products,
            "minutes": minutes,
            "vegetarian": vegetarian,
            "recipe": recipe,
            "error": error,
        },
    )