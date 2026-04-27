# Translation pipeline

Скрипт `translate.py` берёт RU-гайды и переводит их на FR/EN через OpenAI API. Используется в GitHub Actions, можно гонять локально.

## Что нужно один раз настроить

1. **Создай новый OpenAI API-ключ.** Заходишь на https://platform.openai.com/api-keys → Create new secret key. **Используй НОВЫЙ ключ** — старый, что засветился в чате, обязательно отзови (Revoke), если ещё не сделала.
2. **Добавь ключ в GitHub Secrets:**
   - В репозитории на GitHub → Settings → Secrets and variables → Actions → New repository secret
   - Name: `OPENAI_API_KEY`
   - Secret: вставь ключ
3. **Проверь, что Actions включён и может создавать PR:** Settings → Actions → General →
   - Actions permissions: «Allow all actions and reusable workflows»
   - Workflow permissions: «Read and write permissions» + ✅ галочка «Allow GitHub Actions to create and approve pull requests»

## Как запустить перевод (через GitHub Actions)

1. Открой репозиторий на GitHub → вкладка **Actions**
2. Слева выбери workflow **«Translate guides RU → FR»**
3. Нажми **«Run workflow»** (справа)
4. Поля:
   - **files** — оставь пустым, чтобы перевести все непереведённые. Или укажи через запятую: `objection-dorogo,objection-podumat`
   - **model** — оставь по умолчанию `gpt-4o` (баланс цена/качество). Альтернативы:
     - `gpt-4o-mini` — самый дешёвый (~$0.03 за все 7 файлов), но качество скромнее
     - `gpt-5` — лучшее качество, чуть дороже
5. Нажми зелёную **«Run workflow»**
6. Через 2–10 минут (зависит от количества файлов) на вкладке **Pull requests** появится новый PR `🇫🇷 RU → FR translation batch (...)` с переведёнными файлами.
7. Открой PR, прочитай `_guides/fr/_TRANSLATION_LOG.md` — там лог. Если есть «Validation failures» — переведённый файл идёт с пометкой `<!-- TRANSLATION VALIDATION FAILED ... -->` сверху.
8. Если всё ок — мерж в main. GitHub Pages пересоберёт сайт за 1–3 минуты.

## Как запустить локально (необязательно)

```bash
export OPENAI_API_KEY="sk-..."
cd <repo-root>
pip install -r scripts/requirements.txt

# Перевести все непереведённые
python scripts/translate.py \
  --source-lang ru \
  --target-lang fr \
  --prompt prompts/opencode-translate-fr.md \
  --source-dir _guides/ru \
  --target-dir _guides/fr

# Перевести конкретный файл с другой моделью
python scripts/translate.py \
  --source-lang ru \
  --target-lang fr \
  --prompt prompts/opencode-translate-fr.md \
  --source-dir _guides/ru \
  --target-dir _guides/fr \
  --model gpt-5 \
  --files objection-dorogo
```

## Safety guards

Скрипт **никогда** не:
- модифицирует файлы в `_guides/ru/`
- перезаписывает существующие файлы в `_guides/fr/` (если файл уже есть — пропускает)
- удаляет файлы

Перед записью каждого файла прогоняется валидация: должны быть все ключевые поля frontmatter, `lang: fr`, правильный slug, ключевые HTML-блоки (callout, dialog, paris-banner). Если валидация не прошла — файл записывается с пометкой `<!-- TRANSLATION VALIDATION FAILED -->` сверху, чтобы человек обязательно его прочитал перед мержем.

## Ориентировочная стоимость

Один RU-гайд — это ~10K токенов вход (включая system prompt) + ~5K токенов выход.

| Модель | Цена за 7 гайдов |
|---|---|
| `gpt-4o-mini` | ~$0.03 |
| `gpt-4o` | ~$0.50 |
| `gpt-5` | ~$0.40–0.80 |

Все варианты вписываются в твою «$5 на эту задачу».

## Расширение на EN

Когда FR-партия зайдёт хорошо:
1. Создай `prompts/opencode-translate-en.md` (можно скопировать FR-промпт и переделать примеры)
2. Создай новый workflow `.github/workflows/translate-en.yml` — копия `translate-fr.yml` с заменой `--target-lang fr` на `--target-lang en` и пути промпта
3. Slug-map для EN уже зашит в `translate.py`

## Когда что-то пошло не так

- **«OPENAI_API_KEY env var not set»** — забыла добавить секрет, или название неверное
- **«no slug map entry for target lang»** — добавила новый RU-гайд, но не прописала ему target-slug в `SLUG_MAP_FR` (в `translate.py`). Допиши и перезапусти.
- **PR не создался, но переводы в логе видно** — проверь Actions logs на шаге `Create Pull Request`. Скорее всего нет permissions: Settings → Actions → General → Workflow permissions → «Read and write permissions» + галочка «Allow GitHub Actions to create and approve pull requests»
- **«model_not_found» или «model_not_available»** — у твоего OpenAI-аккаунта нет доступа к этой модели. Попробуй `gpt-4o` (доступна почти всем) или `gpt-4o-mini`
- **Validation failures на всех файлах** — модель не следует формату. Попробуй другой model или прочти `prompts/opencode-translate-fr.md` — что-то могло сломаться в промпте
- **«rate_limit_exceeded»** — слишком много параллельных запросов. Скрипт работает последовательно, так что обычно это значит низкий tier у аккаунта. Подожди или upgrade tier
