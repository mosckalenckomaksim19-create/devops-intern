# Тестовое задание DevOps стажёра

Минимальное Python-приложение отвечает `Hello world!` по HTTP на порту **32777**. Docker упаковывает приложение в образ, а Kubernetes Deployment запускает **два Pod по одному контейнеру**. Service типа ClusterIP даёт им общий адрес внутри кластера. Для браузера используется `kubectl port-forward`.

Основной путь выполнения: **Windows → Ubuntu в WSL2 → Docker Desktop с WSL Integration → Minikube с Docker driver**. Все команды ниже выполняются в терминале Ubuntu, кроме блока PowerShell в разделе 1.

## Результат

Приложение собрано в Docker-образ и опубликовано как `xumuk595/devops-hello:1.0.0`. В Minikube успешно запущены две реплики: Deployment показывает `READY 2/2`, обе реплики — `Running` и `READY 1/1`. Service содержит адреса обоих Pod. Страница открывается через port-forward, а 20 запросов к Service изнутри кластера распределились между репликами как 11 и 9.

- [Исходный код на GitHub](https://github.com/mosckalenckomaksim19-create/devops-intern)
- [Образ и теги Docker Hub](https://hub.docker.com/r/xumuk595/devops-hello/tags)
- [Фактические результаты проверки](docs/verification.md)
- [Скриншоты](docs/screenshots/)

Ниже приведены команды воспроизведения и объяснения решений. Для публикации изменённого образа под своим аккаунтом используй собственный Docker Hub username и обнови поле `image` в Deployment.

## Структура

```text
devops-intern/
├── app.py
├── Dockerfile
├── .dockerignore
├── .gitignore
├── .gitattributes
├── README.md
├── k8s/
│   ├── deployment.yaml
│   └── service.yaml
└── docs/
    ├── theory.md
    ├── defense.md
    ├── sql-demo.sql
    ├── architecture.drawio
    ├── architecture.png
    ├── verification.md
    └── screenshots/
        └── README.md
```

[Ответы на 8 вопросов](docs/theory.md) · [Подготовка к защите](docs/defense.md) · [Схема draw.io](docs/architecture.drawio)

## 1. Подготовить Windows и WSL2

В **PowerShell Windows** проверь:

```powershell
wsl --version
wsl --list --verbose
```

Нужен установленный дистрибутив Linux в режиме `VERSION 2`. Если Ubuntu отсутствует, установи её командой `wsl --install -d Ubuntu` (при запросе Windows — с правами администратора), выполни предложенную перезагрузку, открой Ubuntu и создай Linux-пользователя. Если у существующего дистрибутива `VERSION 1`, переведи его командой `wsl --set-version Ubuntu 2`, подставив точное имя из списка. Для обновления WSL: `wsl --update`.

Установи и запусти [Docker Desktop для Windows](https://docs.docker.com/desktop/setup/install/windows-install/). В настройках выбери WSL2 backend, если этот пункт доступен, и включи **Resources → WSL Integration → свой дистрибутив Ubuntu → Apply**. Docker должен работать в режиме Linux containers. [Официальная инструкция интеграции с WSL](https://docs.docker.com/desktop/features/wsl/).

Теперь открой терминал **Ubuntu**, проверь:

```bash
cat /etc/os-release
uname -m
docker version
docker info --format '{{.OSType}}'
```

Ожидается: `docker version` показывает и Client, и Server; последняя команда выводит `linux`. Если есть только Client и ошибка подключения, сначала запусти Docker Desktop и проверь интеграцию с нужным дистрибутивом.

Этот путь использует Docker Engine из Docker Desktop. Если у тебя уже стоит отдельный Engine внутри Ubuntu, сначала разберись, какой daemon используется; не добавляй вторую установку поверх существующей вслепую.

## 2. Поместить проект в WSL и проверить приложение

После установки Git получи проект из публичного репозитория:

```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/mosckalenckomaksim19-create/devops-intern.git
cd devops-intern
```

Если папка проекта уже существует, перейди в неё; повторно клонировать репозиторий не нужно. Альтернатива — скачать ZIP с GitHub и распаковать его. Дальнейшие команды выполняй из папки проекта.

Для Ubuntu установи недостающие утилиты:

```bash
sudo apt-get update
sudo apt-get install -y python3 git curl ca-certificates
python3 app.py
```

В соседнем терминале Ubuntu:

```bash
curl -i http://127.0.0.1:32777/
curl -i http://127.0.0.1:32777/healthz
```

Ожидается `200 OK`, на `/` — `Hello world!`, на `/healthz` — `ok`. После проверки останови приложение через **Ctrl+C**, чтобы освободить порт перед Docker.

### Как устроен app.py

- `ThreadingHTTPServer` принимает HTTP-запросы; обработчик `do_GET` выбирает ответ по пути.
- `0.0.0.0` означает «слушать все IPv4-интерфейсы». В контейнере нельзя ограничиться `127.0.0.1`, иначе обычный доступ по IP Pod не сработает.
- `32777` — реальный порт сокета приложения.
- `/healthz` позволяет Kubernetes проверить, отвечает ли процесс.
- `Instance` показывает hostname: внутри обычного Pod это его имя. Так можно различить реплики.
- Всё работает на стандартной библиотеке Python; файла зависимостей и `pip install` нет.

Это учебный HTTP-сервер для маленького задания. Для промышленного веб-приложения выбирают подходящий сервер и более полную обработку запросов. [Python http.server](https://docs.python.org/3.12/library/http.server.html).

## 3. Создать аккаунт и репозиторий Docker Hub

1. Зарегистрируйся на [Docker Hub](https://hub.docker.com/) и подтверди почту, если сервис попросит.
2. Запомни **username**, а не отображаемое имя и не email.
3. Создай репозиторий **devops-hello** в своём namespace, видимость **Public**. Публичный образ можно скачать из Minikube без настройки `imagePullSecrets`. [Создание репозитория](https://docs.docker.com/docker-hub/repos/create/).

Для исходного образа имя аккаунта — `xumuk595`. Если собираешь и публикуешь свою копию, замени его собственным логином в нижнем регистре:

```bash
export DOCKERHUB_USERNAME='xumuk595'
export IMAGE="${DOCKERHUB_USERNAME}/devops-hello:1.0.0"
printf '%s\n' "$IMAGE"
```

Публиковать образ можно только в namespace, к которому у тебя есть доступ. Переменные живут в текущем терминале; в новом окне эти две строки нужно выполнить снова.

Имя образа состоит из аккаунта, репозитория и версии. Версия `1.0.0` — выбранный тег нашего приложения, а не версия Python.

## 4. Собрать и проверить Docker-образ

```bash
docker build -t "$IMAGE" .
docker run --rm -d --name devops-hello-local -p 127.0.0.1:32777:32777 "$IMAGE"
docker ps --filter name=devops-hello-local
curl -i http://127.0.0.1:32777/
docker logs devops-hello-local
```

Точка в `docker build` задаёт контекст сборки — текущую папку. `.dockerignore` оставляет в нём только файлы приложения и сборки. `--rm` удалит контейнер после остановки, `-d` запускает его в фоне, `--name` даёт удобное имя. В `-p` первый порт принадлежит хосту, второй — контейнеру; здесь оба равны 32777.

Открой в браузере Windows **http://localhost:32777/**. Для WSL маршрут localhost зависит от настроек Windows/WSL; если в Ubuntu `curl` работает, а браузер нет, смотри раздел диагностики.

После проверки сохрани скриншот и останови локальный контейнер:

```bash
docker stop devops-hello-local
```

Это освобождает локальный порт перед `port-forward`; образ остаётся.

### Что делает каждая строка Dockerfile

| Инструкция | Зачем |
| --- | --- |
| `FROM python:3.12-slim` | Базовый Linux-образ с Python; тег семейства может обновляться, это не фиксация по digest |
| `ENV ...` | Выводит логи без буферизации и не создаёт `.pyc` |
| `WORKDIR /app` | Задаёт рабочий каталог для дальнейших инструкций и запуска |
| `COPY --chown=10001:10001 ...` | Копирует код и задаёт владельца файла |
| `USER 10001:10001` | Запускает приложение от непривилегированного числового UID/GID |
| `EXPOSE 32777` | Документирует порт; не публикует его на хосте и не запускает сервер |
| `CMD ["python", "app.py"]` | Задаёт команду запуска в exec-форме без дополнительной оболочки |

## 5. Опубликовать образ

```bash
docker login
docker push "$IMAGE"
```

Выполни предложенный CLI вход через браузер. Если используешь вход по username, можно выполнить `docker login --username "$DOCKERHUB_USERNAME"` и ввести токен в запросе пароля. Пароли и токены не добавляются в исходники.

`push` отправляет слои образа и его манифест в registry. В конце успешной публикации Docker покажет digest. Открой свой репозиторий Docker Hub и проверь тег `1.0.0`; сохрани скриншот. [Документация push](https://docs.docker.com/docker-hub/repos/manage/hub-images/push/).

Если изменишь код после публикации, используй новый тег, например `1.0.1`, и обнови YAML. При `IfNotPresent` повторное использование старого тега может оставить кэшированный образ на узле.

## 6. Установить Minikube в Ubuntu

Следуй [официальной инструкции Minikube](https://minikube.sigs.k8s.io/docs/start/): выбирай **Linux**, архитектуру из `uname -m` и установку **Binary**. Хотя компьютер работает на Windows, команды здесь выполняются внутри Linux в WSL.

Для **x86_64**:

```bash
mkdir -p ~/Downloads/minikube-install
cd ~/Downloads/minikube-install
curl -fLO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
minikube version
cd ~/projects/devops-intern
```

Для **aarch64/arm64** используй `minikube-linux-arm64` в URL и имени файла команды `install`. Не запускай обе версии. Загружается текущий stable; фактическую версию сохрани для отчёта.

Создай отдельный профиль кластера:

```bash
minikube start -p devops-intern --driver=docker --cpus=2 --memory=3072
minikube status -p devops-intern
minikube -p devops-intern kubectl -- get nodes
```

Minikube создаёт локальный узел Kubernetes с помощью Docker. Docker driver — способ создать узел; это не означает, что внутри Kubernetes обязательно используется Docker Engine как runtime. Узлу выделяется 2 CPU и 3072 MiB памяти; Docker/WSL должны располагать этим объёмом плюс ресурсами для остальной системы. В норме Node имеет состояние `Ready`. Запускай `minikube start` от обычного Linux-пользователя, без `sudo`.

Чтобы не устанавливать отдельный kubectl, используй встроенный:

```bash
alias kubectl='minikube -p devops-intern kubectl --'
kubectl config current-context
```

`kubectl` — клиент Kubernetes API. Здесь alias направляет его в профиль `devops-intern`. Выполняй строку alias **в каждом новом терминале Ubuntu**, где нужны команды kubectl. Полный эквивалент `kubectl get pods` — `minikube -p devops-intern kubectl -- get pods`.

## 7. Настроить и применить Deployment и Service

В `k8s/deployment.yaml` указан опубликованный образ:

```yaml
image: xumuk595/devops-hello:1.0.0
```

Для запуска исходного решения менять его не требуется. Если публикуешь собственную версию, укажи её точное имя и тег. Kubernetes не подставляет переменные оболочки в YAML автоматически.

Проверь и примени манифесты:

```bash
kubectl apply --dry-run=server -f k8s/
kubectl apply -f k8s/
kubectl rollout status deployment/hello-world --timeout=180s
kubectl get deployment hello-world
kubectl get pods -l app=hello-world -o wide
kubectl get service hello-world
kubectl get endpointslices -l kubernetes.io/service-name=hello-world -o wide
```

Dry-run проверяет манифесты на сервере без сохранения объектов. Он не проверяет возможность скачать образ и не запускает контейнер. `apply` сохраняет желаемое состояние. `rollout status` ждёт завершения развёртывания.

Критерии: у Deployment `READY 2/2`, `UP-TO-DATE 2`, `AVAILABLE 2`; два Pod в `Running`, у каждого `READY 1/1`; Service — `ClusterIP` с портом `80/TCP`. В EndpointSlice должны быть адреса обеих реплик; при необходимости проверь готовность подробным выводом `kubectl get endpointslices -l kubernetes.io/service-name=hello-world -o yaml`.

### Почему YAML устроен именно так

- `replicas: 2` задаёт два экземпляра Pod. Deployment управляет ReplicaSet, который поддерживает нужное число Pod.
- `template` описывает будущие Pod. Его метка `app: hello-world` совпадает с селекторами Deployment и Service.
- `Service.spec.selector` находит Pod по метке, а не по их сгенерированным именам.
- `containerPort: 32777` назван `http`; Service направляет запросы на этот именованный порт через `targetPort: http`.
- `Service.port: 80` — порт общего адреса сервиса внутри кластера. Приложение по-прежнему слушает 32777.
- ClusterIP достаточен для внутреннего доступа, а внешний просмотр в этом задании делает `port-forward`.
- `readinessProbe` убирает неготовую реплику из обычного трафика Service. `livenessProbe` позволяет перезапустить зависший контейнер после повторных неудач.
- `requests` нужны планировщику для размещения, `limits` ограничивают ресурсы контейнера. `50m` CPU — 0,05 ядра; превышение лимита CPU ведёт к ограничению, лимита памяти может привести к OOM-завершению.

Две реплики на одном узле показывают восстановление Pod и работу сервиса с несколькими экземплярами, но не защищают от потери самого узла.

## 8. Открыть приложение через port-forward

В отдельном терминале Ubuntu:

```bash
minikube -p devops-intern kubectl -- port-forward service/hello-world 32777:80 --address=127.0.0.1
```

Оставь команду работающей. Она занимает локальный порт 32777, находит Pod через Service и переводит сервисный порт 80 в целевой 32777. Ожидаемая строка: `Forwarding from 127.0.0.1:32777 -> 32777`.

В другом терминале:

```bash
curl -i http://127.0.0.1:32777/
```

Открой в браузере Windows **http://localhost:32777/** и сделай скриншот, где видны адрес, `Hello world!` и имя экземпляра.

Важная тонкость для защиты: **port-forward к Service выбирает один подходящий Pod**. Это диагностический туннель через Kubernetes API к Pod, а не обычная балансировка через ClusterIP. Обновление страницы не обязано переключать реплики. Если выбранный Pod исчезнет, туннель может завершиться — запусти команду снова. [Port forwarding в Kubernetes](https://kubernetes.io/docs/tasks/access-application-cluster/port-forward-access-application-cluster/).

Для доказательства работоспособности каждой реплики можно по очереди пробросить порт непосредственно к каждому Pod (имя взять из `kubectl get pods`):

```bash
kubectl port-forward pod/REPLACE_WITH_FIRST_POD_NAME 32778:32777
```

Открыть `http://localhost:32778/`, остановить Ctrl+C, повторить для второго имени. Это дополнительная проверка, основной обязательный туннель выше направлен к Service.

## 9. Проверить доступ через настоящий Service внутри кластера

Убедись, что alias kubectl задан. Команда запустит Python в одной из реплик и сделает 20 отдельных HTTP-запросов к DNS-имени сервиса. Вставь весь блок, включая последнюю строку `PY`:

```bash
kubectl exec -i deployment/hello-world -- python - <<'PY'
from collections import Counter
from urllib.request import urlopen

instances = Counter()
for _ in range(20):
    with urlopen("http://hello-world", timeout=5) as response:
        instances[response.headers["X-Instance"]] += 1
        response.read()
print(instances)
PY
```

Здесь запросы действительно идут по адресу Service на порт 80 к готовым Pod. При нормальной работе можно увидеть два имени в счётчике, но строгого чередования и гарантии «оба за 20 запросов» нет. Два готовых адреса EndpointSlice и прямые проверки Pod дополняют эту демонстрацию. [Service в Kubernetes](https://kubernetes.io/docs/concepts/services-networking/service/).

SQL для практического приложения не требуется; отдельные примеры находятся в `docs/sql-demo.sql`.

## 10. Схема и скриншоты

Открой [app.diagrams.net](https://app.diagrams.net/), выбери хранение на устройстве и **File → Open From → Device**, затем `docs/architecture.drawio`. Можно менять подписи и экспортировать PNG через **File → Export as → PNG**. Исходный `.drawio` обязательно оставь в репозитории.

![Схема контейнеров и сервиса](docs/architecture.png)

На схеме синим показан обычный трафик через Service, оранжевым — port-forward к выбранному Pod. Service — сетевой объект Kubernetes, у него нет собственного контейнера приложения.

Сохрани настоящие скриншоты по [чек-листу](docs/screenshots/README.md). Здесь нет заранее изготовленных «скриншотов успешного Minikube»: их нужно получить после запуска своего стенда.

## 11. Опубликовать открытый Git-репозиторий

На GitLab или GitHub создай **пустой Public-репозиторий**, например `devops-intern`, без автоматически созданных README и `.gitignore`. Docker Hub хранит образы, Git-репозиторий — исходники и документы: это две разные публикации.

В папке проекта:

```bash
git status
```

Если это ещё не репозиторий, выполни `git init -b main`. Если скопировал подготовленный проект вместе с `.git`, повторный init не нужен. При отсутствии настроенной личности задай имя и email через `git config user.name` и `git config user.email` с собственными значениями.

Добавь скриншоты и проверь, что отчёт проверки соответствует текущему запуску. Затем:

```bash
git add app.py Dockerfile .dockerignore .gitignore .gitattributes README.md k8s docs
git diff --cached --stat
git diff --cached
git commit -m "Add hello-world app and Kubernetes deployment"
```

Проверь содержимое перед публикацией. Замени URL ниже реальным адресом созданного репозитория. Для собственной копии используй адрес своего репозитория.

```bash
git remote add origin https://github.com/mosckalenckomaksim19-create/devops-intern.git
git push -u origin main
```

При запросе аутентификации используй способ своего хостинга: credential manager, токен или настроенный SSH. Если `origin` уже есть, сначала посмотри `git remote -v`, а не добавляй его повторно.

Проверь ссылку в окне браузера без авторизации: исходники, теория, схема и скриншоты должны открываться. Так проверяется требование об открытом репозитории.

## 12. Что приложить при сдаче

- Ссылку на публичный Git-репозиторий.
- Ссылку на Docker Hub с тегом образа.
- `docs/architecture.drawio` и при необходимости его экспорт.
- Скриншоты: Docker Hub, две реплики Kubernetes, Service/EndpointSlice, работающий port-forward и браузер.
- В README — реальные версии, шаги запуска и результат проверки.

Проверь, что в манифесте нет `YOUR_DOCKERHUB_USERNAME`, имя образа совпадает с Docker Hub, Deployment содержит две реплики, скриншоты отражают итоговое состояние.

## Диагностика частых ошибок

| Симптом | Что проверить |
| --- | --- |
| Docker не найден в WSL | Docker Desktop запущен, WSL Integration включена для нужного дистрибутива; переоткрой терминал |
| Cannot connect to Docker daemon | Вывод `docker version`, состояние Desktop, выбранный Docker context |
| Minikube не стартует | `docker info`, свободная память и диск, `minikube logs -p devops-intern --problems`; текст первой ошибки |
| ImagePullBackOff | `kubectl describe pod ИМЯ`: правильный логин и тег, Public-образ, доступ к Docker Hub и лимиты скачивания |
| CrashLoopBackOff | `kubectl logs ИМЯ`, `kubectl logs ИМЯ --previous`, события из `kubectl describe pod ИМЯ` |
| Pod Pending | `kubectl describe pod ИМЯ`: хватает ли CPU/памяти и готов ли Node |
| Service не отвечает | Совпадают ли labels/selector, readiness, EndpointSlice, `port`/`targetPort` |
| Address already in use | Останови прежний app.py, Docker-контейнер или туннель; в WSL проверь `ss -lntp` |
| kubectl смотрит не туда | Используй полный вызов `minikube -p devops-intern kubectl -- ...` |

Если `curl` внутри WSL работает, а браузер Windows не открывает localhost, сначала попробуй оба адреса `http://localhost:32777/` и `http://127.0.0.1:32777/`, проверь занятость порта в Windows, firewall и настройки localhost forwarding WSL. Для изолированной проверки маршрута можно перезапустить port-forward с `--address=0.0.0.0`, узнать IPv4 Ubuntu командой `hostname -I` и открыть `http://WSL_IP:32777/`. Этот вариант слушает все интерфейсы, поэтому используй его только в доверенной локальной среде и после проверки верни `127.0.0.1`.

## Завершение работы

Останови туннель Ctrl+C, затем:

```bash
minikube stop -p devops-intern
```

Кластер сохранится для следующего запуска. Полное удаление именно учебного профиля, когда он больше не нужен: `minikube delete -p devops-intern`. Удалять кластер перед скриншотами не нужно.
