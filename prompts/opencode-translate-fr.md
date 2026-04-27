# Opencode — техзадание на перевод RU → FR

Этот файл — единственный источник правды для перевода гайдов с русского на французский. Если ты opencode/Claude/любой агент, читающий это — действуй ровно по этим правилам. Если что-то не покрыто — сначала спроси, не выдумывай.

---

## Миссия

Перевести 7 гайдов из `_guides/ru/` на французский. Создать 7 новых файлов в `_guides/fr/`. **Не трогать ни один существующий файл.** Это пилотный проект перед массовым автопереводом, поэтому каждый файл должен быть production-ready.

Аудитория FR — франкоязычные предприниматели и продажники (Франция в первую очередь, Бельгия/Швейцария — бонусом). Тон — `tu` (informal), личный, как у эталонного автора Jean-Luc Médéric.

---

## ⛔ Жёсткие правила безопасности

1. **Никогда** не модифицируй файлы в `_guides/ru/`. Read-only.
2. **Никогда** не модифицируй `_layouts/`, `_includes/`, `assets/`, `_config.yml`. Read-only.
3. **Только** создавай новые файлы в `_guides/fr/`.
4. Если файл `_guides/fr/<slug>.md` уже существует — **пропусти его**, не перезаписывай. Логируй в stdout: `SKIPPED: <slug> (already exists)`.
5. Если не понимаешь, как перевести термин или конструкцию — оставь в комментарии `<!-- TODO: translate -->` и переходи дальше. Лучше пометить, чем выдумать.
6. **Не используй** Google Translate / DeepL API через интернет. Перевод делает только модель напрямую (Claude/GPT через основной API).

---

## Структура исходника

Каждый файл `_guides/ru/<slug>.md` имеет:
- YAML frontmatter (заголовок, описание, FAQ, slug, lang, и т.д.)
- Markdown тело со встроенным HTML (`<div class="callout">`, `<div class="dialog">`, и т.д.)

Frontmatter и HTML-классы — критичны. Дизайн-система основана на этих классах. **Не меняй их.**

---

## Маппинг slug-ов RU → FR

Используй ровно эти slug-и для целевых файлов:

| RU исходник | FR target | Целевой URL |
|---|---|---|
| `objection-dorogo.md` | `objection-c-est-cher.md` | `/fr/guides/objection-c-est-cher/` |
| `objection-podumat.md` | `objection-je-vais-reflechir.md` | `/fr/guides/objection-je-vais-reflechir/` |
| `objection-pozhe.md` | `objection-plus-tard.md` | `/fr/guides/objection-plus-tard/` |
| `objection-net-vremeni.md` | `objection-pas-le-temps.md` | `/fr/guides/objection-pas-le-temps/` |
| `objection-nado-posovetovatsya.md` | `objection-je-dois-en-parler.md` | `/fr/guides/objection-je-dois-en-parler/` |
| `closing-questions.md` | `questions-de-cloture.md` | `/fr/guides/questions-de-cloture/` |
| `prospecting-plan.md` | `plan-de-prospection.md` | `/fr/guides/plan-de-prospection/` |
| `kp-ghosting.md` | `client-disparu-apres-devis.md` | `/fr/guides/client-disparu-apres-devis/` |

Slug-и: только ASCII, без диакритики, через дефис.

---

## Правила перевода frontmatter

```yaml
---
title: "« Запрос клиента » — короткий рабочий ответ"      # FR-кавычки « » с пробелами, 40-60 символов
description: "Описание с ключом и обещанием. До 160 символов."  # На французском, естественная формулировка
promise: "En X minutes tu auras [résultat concret] — sans [peur principale du client]."
category: "Objections"                # см. таблицу категорий ниже
chips:
  - "Objections"
  - "Script inclus"                   # короткие FR-эквиваленты
  - "X min de lecture"
hero_emoji: "💸"                      # БЕЗ изменений, оставь как в исходнике
hero_caption: "Подзаголовок-приманка"  # Перевод
author: "Jean-Luc Médéric"            # БЕЗ изменений
date: 2026-04-27                      # БЕЗ изменений (или текущая дата перевода)
reading_time: "X min de lecture"
lang: fr                              # ← Замени с ru на fr
slug: <slug-fr-из-таблицы>            # ← Возьми из таблицы маппинга
faq:                                  # Переведи все 4 вопроса и ответы
  - q: "..."
    a: "..."
hreflang_alt:                         # ← НОВОЕ ПОЛЕ. Добавь альтернативные языки
  ru: /ru/guides/<slug-ru>/
  en: /en/guides/<slug-en>/
---
```

### Маппинг категорий

| RU | FR |
|---|---|
| Возражения | Objections |
| Закрытие | Clôture |
| Воронка | Pipeline |
| Проспектинг | Prospection |

### Маппинг chips

| RU фраза | FR фраза |
|---|---|
| Возражения | Objections |
| Закрытие | Clôture |
| Скрипт внутри | Script inclus |
| Скрипт + диалог | Script + dialogue |
| Шаблон + диалог | Modèle + dialogue |
| План + чек-листы | Plan + checklists |
| Проспектинг | Prospection |
| X мин чтения | X min de lecture |

---

## Правила перевода тела статьи

### Тон и обращение

- На французском **`tu`** (informal). Никогда не `vous`. Это критично для бренд-голоса.
- Личный голос. Прямое обращение. Как тренер-ровесник.
- Французский разговорный, не академический. Без `nous allons examiner`, `il convient de noter` и подобной канцелярщины.
- Короткие предложения. Абзацы 1–3 предложения максимум.

### Терминология (фиксированная)

| RU | FR |
|---|---|
| «Менеджер» (в диалогах) | « Vendeur » (или « Commercial » в B2B-контексте) |
| Клиент | Client |
| Сделка | Affaire / vente |
| Проспектинг | Prospection |
| Возражение | Objection |
| ЛПР | décideur |
| Холодный звонок | appel à froid |
| Closing / закрытие | clôture |
| Скрипт | script |
| Воронка | pipeline / entonnoir |

### Кавычки

- Французские: `« texte »` (с неразрывным пробелом внутри, но в Markdown можно обычным пробелом)
- Никогда не `"texte"` в основном тексте

### Цитаты Michael Bang

Оставь английский оригинал в `<em>...</em>`, под ним добавь французский перевод в скобках:

```html
<div class="callout is-quote">
<p class="callout-title">Citation</p>
<p><em>« Original English quote from Bang. »</em></p>
<p>(« Traduction libre : французский перевод. »)</p>
<cite>— Michael Bang, leçon #15 « Objection Handling »</cite>
</div>
```

### Цены и валюта

- Евро остаются евро: `€18,000` → `18 000 €` (французский формат: пробел как разделитель тысяч, € после числа)
- Сроки: `90 дней` → `90 jours`
- Проценты: те же, формат тот же

### Имена и реалии

- `Jean-Luc Médéric` — без изменений
- `Michael Bang` — без изменений
- `Golden Key of Sales` — оставь английское название, в первом упоминании можно дать перевод в скобках: `Golden Key of Sales (« la clé d'or de la vente »)`
- Мастер-класс 9–10 мая в Париже → `masterclass des 9 et 10 mai à Paris`

### HTML-структура

**Нельзя** менять. Каждый блок исходника соответствует ровно одному блоку перевода:

- `<div class="callout is-key">` ↔ `<div class="callout is-key">`
- `<div class="callout is-tip">` ↔ `<div class="callout is-tip">`
- `<div class="callout is-warn">` ↔ `<div class="callout is-warn">`
- `<div class="callout is-quote">` ↔ `<div class="callout is-quote">`
- `<div class="bad-example">` ↔ `<div class="bad-example">`
- `<div class="good-example">` ↔ `<div class="good-example">`
- `<div class="phrase-card">` ↔ `<div class="phrase-card">`
- `<div class="dialog">` ↔ `<div class="dialog">`
  - `<p class="dialog-line">` (vendeur) и `<p class="dialog-line is-them">` (client) — без изменений
  - Внутри: `<span class="who">Vendeur:</span><span class="what">текст</span>`
- `<ul class="check">` ↔ `<ul class="check">`

### Inline-баннер CTA

В исходнике: `{% include paris-banner.html utm_medium="guide_inline" %}`

В переводе: **точно такая же строка**. Liquid-template сам подхватит `page.lang: fr` и подставит французский баннер + UTM с `utm_campaign=fr`.

### Внутренние ссылки на другие гайды

Когда видишь в исходнике:
```
[«Надо подумать»]({{ site.baseurl }}/ru/guides/objection-podumat/)
```

Переведи на FR-эквивалент по таблице slug-ов:
```
[« Je vais réfléchir »]({{ site.baseurl }}/fr/guides/objection-je-vais-reflechir/)
```

Если ссылка ведёт на гайд, который ещё не переведён (но в нашем списке) — всё равно ставь FR-ссылку (когда тот гайд переведётся, ссылка заработает).

---

## Заголовки FR (для title в frontmatter)

Используй естественные французские поисковые запросы. Не дословный перевод, а как реальный французский продажник это бы загуглил.

| RU title | FR title |
|---|---|
| « Дорого » — как ответить, чтобы клиент не сорвался | « C'est trop cher » — comment répondre sans perdre la vente |
| « Мне надо подумать » — что отвечать, чтобы клиент не пропал | « Je vais réfléchir » — comment éviter que le client disparaisse |
| « Давайте позже » — что отвечать, чтобы клиент не ушёл к конкуренту | « Plus tard » — comment ne pas perdre le client face à la concurrence |
| « Нет времени » — что отвечать, чтобы не звучать навязчиво | « J'ai pas le temps » — comment répondre sans être lourd |
| « Мне надо посоветоваться » — как не потерять сделку в чужих руках | « Je dois en parler » — comment ne pas perdre la vente entre des mains tierces |
| Закрытие сделки без давления — 3 типа вопросов, которые работают | Clôturer une vente sans pression — 3 types de questions qui marchent |
| План проспектинга — 5 каналов, которые дают стабильный поток лидов | Plan de prospection — 5 canaux pour un flux stable de leads |
| « Клиент пропал после КП » — что писать и когда звонить, не выбешивая | « Le client a disparu après le devis » — quoi écrire et quand appeler, sans agacer |

---

## Validation checklist (выполняй после каждого файла)

После генерации каждого файла `_guides/fr/<slug>.md` проверь сам себя:

- [ ] Frontmatter содержит все обязательные поля: `title`, `description`, `promise`, `category`, `chips`, `hero_emoji`, `hero_caption`, `author`, `date`, `reading_time`, `lang: fr`, `slug` (FR), `faq` (4 шт), `hreflang_alt`
- [ ] `lang: fr` (не `ru`!)
- [ ] `slug` соответствует таблице маппинга
- [ ] Количество HTML-блоков в FR = количество в RU. Сверь:
  - `<div class="callout is-key">` — должен быть ровно 1
  - `<div class="bad-example">` — столько же, сколько в RU
  - `<div class="good-example">` — столько же
  - `<div class="phrase-card">` — столько же
  - `<div class="dialog">` — ровно 1
  - `{% include paris-banner.html %}` — ровно 1
- [ ] В диалоге используется `Vendeur:` (не `Жан-Люк`, не `Manager`, не `Менеджер`)
- [ ] Все внутренние ссылки `[...]({{ site.baseurl }}/...)` ведут на `/fr/guides/`, не `/ru/guides/`
- [ ] Тон `tu` (никаких `vous` в основном тексте — допустимо только в специфических контекстах вроде сценариев формальной переписки)
- [ ] Нет следов русского текста (особенно в диалогах и cite)
- [ ] FAQ: 4 вопроса, переведены, без TODO

Если хоть одна галочка не стоит — не помечай файл готовым. Пометь `<!-- VALIDATION: <причина> -->` и переходи к следующему.

---

## Output format и логирование

В конце работы создай файл `_guides/fr/_TRANSLATION_LOG.md` со списком:

```
# Translation log RU → FR
Date: YYYY-MM-DD
Source commit: <SHA>
Model: <claude-model-name>

## Translated successfully
- objection-c-est-cher.md (from objection-dorogo.md)
- ...

## Skipped
- <slug> (reason: already exists / validation failed / other)

## Validation failures (need human review)
- <slug>: <причина>
```

---

## Что делать если застрял

Если конкретная фраза не переводится естественно (русская идиома, ситуация-специфичный сленг) — переведи приблизительно и оставь комментарий:

```html
<!-- TRANSLATOR NOTE: оригинал «X», перевёл как «Y», возможно нужна правка -->
```

Не выдумывай факты, цифры, кейсы. Если в RU `«€18,000»` — в FR `«18 000 €»`. Не меняй сумму.

---

## Контекст метода (для понимания)

Все статьи учат методу **Golden Key of Sales** Михаэля Бэнга — 6-шаговый процесс продажи:

1. Prospecting — prospection
2. Relationship Building — création de relation / rapport
3. Qualifying — qualification
4. Presentation — présentation
5. Objection Handling — traitement des objections
6. Closing — clôture

Если в RU встречается отсылка к этим шагам, используй FR-термины из таблицы.
